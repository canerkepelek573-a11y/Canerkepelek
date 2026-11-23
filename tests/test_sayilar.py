import unittest

from derin.sayilar import SeslendirmeMetniHatasi, cevir, kontrol, sayi_yazi, sira_yazi


class SayiYazi(unittest.TestCase):
    def test_tam_sayilar(self):
        ornekler = {
            0: "sıfır",
            7: "yedi",
            10: "on",
            11: "on bir",
            40: "kırk",
            100: "yüz",
            101: "yüz bir",
            365: "üç yüz altmış beş",
            1000: "bin",
            1001: "bin bir",
            1500: "bin beş yüz",
            1947: "bin dokuz yüz kırk yedi",
            1959: "bin dokuz yüz elli dokuz",
            2000: "iki bin",
            10000: "on bin",
            12000: "on iki bin",
            100000: "yüz bin",
            1250000: "bir milyon iki yüz elli bin",
            2_000_000_000: "iki milyar",
        }
        for sayi, beklenen in ornekler.items():
            self.assertEqual(sayi_yazi(sayi), beklenen, sayi)

    def test_sira_sayilari(self):
        ornekler = {
            1: "birinci", 2: "ikinci", 3: "üçüncü", 4: "dördüncü", 5: "beşinci", 6: "altıncı",
            7: "yedinci", 8: "sekizinci", 9: "dokuzuncu", 10: "onuncu", 14: "on dördüncü",
            20: "yirminci", 21: "yirmi birinci", 30: "otuzuncu", 40: "kırkıncı", 50: "ellinci",
            60: "altmışıncı", 100: "yüzüncü", 1000: "bininci",
        }
        for sayi, beklenen in ornekler.items():
            self.assertEqual(sira_yazi(sayi), beklenen, sayi)


class Cevir(unittest.TestCase):
    def esit(self, girdi, beklenen):
        self.assertEqual(cevir(girdi), beklenen)
        kontrol(cevir(girdi))

    def test_yillar_ve_ekler(self):
        self.esit("1959 yılının şubat ayında", "bin dokuz yüz elli dokuz yılının şubat ayında")
        self.esit("1947'de bulundu.", "bin dokuz yüz kırk yedide bulundu.")
        self.esit("1990'larda", "bin dokuz yüz doksanlarda")
        self.esit("4'ü de öldü", "dördü de öldü")
        self.esit("9 kişi", "dokuz kişi")

    def test_binlik_ayrac_ve_ondalik(self):
        self.esit("10.000 yıl", "on bin yıl")
        self.esit("12.000 yıllık", "on iki bin yıllık")
        self.esit("3,5 km yürüdüler", "üç buçuk kilometre yürüdüler")
        self.esit("3,05 oranında", "üç virgül sıfır beş oranında")
        self.esit("12,25 metre", "on iki virgül yirmi beş metre")
        self.esit("1,5 km", "bir buçuk kilometre")

    def test_yuzde(self):
        self.esit("%40'ı inanmıyor", "yüzde kırkı inanmıyor")
        self.esit("% 3,5", "yüzde üç buçuk")

    def test_negatif_ve_derece(self):
        self.esit("-30 derecede", "eksi otuz derecede")
        self.esit("sıcaklık -25 °C idi", "sıcaklık eksi yirmi beş derece idi")

    def test_sira_ve_roma(self):
        self.esit("21. yüzyıl", "yirmi birinci yüzyıl")
        self.esit("Adem'den sonraki 7. kuşak", "Adem'den sonraki yedinci kuşak")
        self.esit("II. Dünya Savaşı", "İkinci Dünya Savaşı")
        self.esit("XIV. Louis", "On Dördüncü Louis")

    def test_cumle_sonu_sayi_sira_sayisi_olmaz(self):
        self.esit("Toplam 365. Sonra kayboldu.", "Toplam üç yüz altmış beş. Sonra kayboldu.")

    def test_kisaltma_saat_aralik(self):
        self.esit("M.Ö. 300 yılında", "milattan önce üç yüz yılında")
        self.esit("saat 23:30 sularında", "saat yirmi üç otuz sularında")
        self.esit("1959-1960 yılları", "bin dokuz yüz elli dokuz ile bin dokuz yüz altmış yılları")
        self.esit("Dr. Vozrojdenny", "Doktor Vozrojdenny")

    def test_kontrol_yakalar(self):
        with self.assertRaises(SeslendirmeMetniHatasi):
            kontrol("Tam 1959 yılında")
        with self.assertRaises(SeslendirmeMetniHatasi):
            kontrol("ve/veya")


if __name__ == "__main__":
    unittest.main()
