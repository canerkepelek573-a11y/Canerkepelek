#!/usr/bin/env bash
# Önizleme karelerini, özeti ve açıklamayı bolumler/<x>/onizleme/ altına koyup depoya gönderir.
# Önce dalın en güncel hâline geçilir (cikti/ git dışıdır, etkilenmez); böylece başka bir
# çalıştırmanın önizleme commit'iyle çakışma olmaz.
set -euo pipefail
yol="$1"; ad=$(basename "$yol"); dal="${GITHUB_REF_NAME}"
git config user.name "github-actions[bot]"
git config user.email "41898299+github-actions[bot]@users.noreply.github.com"
for deneme in 1 2 3 4; do
  git fetch -q origin "$dal"
  git reset -q --hard "origin/$dal"
  mkdir -p "$yol/onizleme"
  rm -f "$yol"/onizleme/*
  cp cikti/"$ad"/onizleme/* "$yol/onizleme/" 2>/dev/null || true
  cp cikti/"$ad"/kapak.jpg cikti/"$ad"/ozet.json "$yol/onizleme/" 2>/dev/null || true
  cp cikti/"$ad"/ana/aciklama.txt cikti/"$ad"/ana/kaynaklar.txt "$yol/onizleme/" 2>/dev/null || true
  git add -A "$yol/onizleme"
  [ -f "$yol/yuklendi.json" ] && git add "$yol/yuklendi.json"
  if git diff --cached --quiet; then echo "Değişiklik yok"; exit 0; fi
  git commit -q -m "Önizleme: $ad"
  if git push -q origin "HEAD:$dal"; then echo "Önizleme kaydedildi"; exit 0; fi
  sleep $((deneme * 5))
done
echo "Önizleme gönderilemedi" >&2; exit 1
