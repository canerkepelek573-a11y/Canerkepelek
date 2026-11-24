import tempfile
import unittest
from pathlib import Path

from derin import video


def _zaman(paragraf_sayisi: int = 12) -> dict:
    """Her paragrafta iki cümle ve iki görsel olan sahte zaman çizelgesi (ağ ve ffmpeg gerekmez)."""
    paragraflar, an = [], 0.4
    for i in range(paragraf_sayisi):
        uzunluk = 6.0 + (i % 5) * 3.1
        orta = an + uzunluk / 2
        paragraflar.append({
            "sira": i, "baslangic": an, "bitis": an + uzunluk,
            "cumleler": [{"baslangic": an, "bitis": orta - 0.3}, {"baslangic": orta, "bitis": an + uzunluk}],
            "goster": [["Kelime.", an, orta - 0.3], ["Kelime", orta, an + uzunluk]],
            "gorseller": [{"kaynak": "yerel", "dosya": "{foto}", "lisans": "test"}] * 2,
        })
        an += uzunluk + 0.55
    return {"sure": round(an, 3), "paragraflar": paragraflar}


class SahnePlani(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        kok = Path(self.gecici.name)
        foto = kok / "foto.jpg"
        foto.write_bytes(b"\xff\xd8\xff")       # yalnızca var olması yeterli (çözülmüyor, kopyalanmıyor)
        self.zaman = _zaman()
        for p in self.zaman["paragraflar"]:
            p["gorseller"] = [{**g, "dosya": str(foto)} for g in p["gorseller"]]
        self.plan = video.plan_hazirla(self.zaman, "ana", kok / "ana", son_kart_sure=15.0,
                                       son_kart={"kaynak": "kart", "baslik": "Son"})

    def tearDown(self):
        self.gecici.cleanup()

    def test_kareler_ardisik(self):
        """Her sahnenin ofs_kare değeri önceki sahnelerin kare toplamıdır (yazılar bu zamana göre basılır)."""
        ofs = 0
        for s in self.plan["sahneler"]:
            self.assertEqual(s["ofs_kare"], ofs)
            self.assertGreaterEqual(s["kare"], 1)
            ofs += s["kare"]
        self.assertAlmostEqual(ofs / video.FPS, self.plan["toplam"], delta=2 / video.FPS)

    def test_dilimler_her_sahneyi_bir_kez_kapsar(self):
        for adet in (1, 2, 3, 4, 6):
            dilimler = [video.dilim(self.plan, no, adet) for no in range(1, adet + 1)]
            hepsi = [k for d in dilimler for k in d]
            self.assertEqual(hepsi, list(range(len(self.plan["sahneler"]))), adet)

    def test_dilimler_dengeli(self):
        toplam = sum(s["kare"] for s in self.plan["sahneler"])
        en_uzun = max(s["kare"] for s in self.plan["sahneler"])
        for no in range(1, 5):
            kare = sum(self.plan["sahneler"][k]["kare"] for k in video.dilim(self.plan, no, 4))
            self.assertLessEqual(abs(kare - toplam / 4), en_uzun)

    def test_gecersiz_dilim(self):
        with self.assertRaises(ValueError):
            video.dilim(self.plan, 0, 4)
        with self.assertRaises(ValueError):
            video.dilim(self.plan, 5, 4)


if __name__ == "__main__":
    unittest.main()
