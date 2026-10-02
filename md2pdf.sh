#!/usr/bin/env bash
# md2pdf.sh — แปลง Markdown (export จาก Docs) เป็น PDF ฟอนต์ TH Sarabun New พร้อมสมการ LaTeX
#
# ใช้:  ./md2pdf.sh รายงาน.md [รายงาน.pdf]
# ตัวแปรที่ปรับได้ (ใส่หน้าคำสั่ง):
#   IMG_DIR=./images   โฟลเดอร์ภาพ ไฟล์ชื่อ <blob-id>.png  (ค่าเริ่มต้น: images ข้างไฟล์ .md)
#   FONT="TH Sarabun New"   ฟอนต์หลัก (ต้องติดตั้งในเครื่องแล้ว)
#   FONT_PT=16         ขนาดตัวอักษรเนื้อความ (pt)
#
# ต้องมี: pandoc, xelatex (MacTeX / TeX Live), perl, ฟอนต์ TH Sarabun New
set -euo pipefail

IN="${1:-}"; [[ -f "$IN" ]] || { echo "ใช้: $0 input.md [output.pdf]" >&2; exit 1; }
OUT="${2:-${IN%.*}.pdf}"
IN_DIR="$(cd "$(dirname "$IN")" && pwd)"
IMG_DIR="${IMG_DIR:-$IN_DIR/images}"
FONT="${FONT:-TH Sarabun New}"
FONT_PT="${FONT_PT:-16}"
LEAD_PT=$(( FONT_PT * 14 / 10 ))   # ระยะบรรทัด = 1.4 เท่า กันสระ/วรรณยุกต์ชน

for c in pandoc xelatex perl; do
  command -v "$c" >/dev/null || { echo "ไม่พบคำสั่ง $c — ติดตั้งก่อน (brew install pandoc; brew install --cask mactex-no-gui)" >&2; exit 1; }
done
if command -v fc-list >/dev/null && [[ -z "$(fc-list "$FONT" 2>/dev/null)" ]]; then
  echo "คำเตือน: ไม่พบฟอนต์ \"$FONT\" ในระบบ (ติดตั้งแล้วรันใหม่ หรือกำหนด FONT=...)" >&2
fi

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1) เตรียม Markdown:
#    - บล็อก ```latex ... ```  ->  $$ ... $$ (สมการ)
#    - ![alt](blob/ID)         ->  ![alt]($IMG_DIR/ID.png){width=85%}  (ไม่มีไฟล์ภาพ = ข้ามและเตือน)
#    - สัญลักษณ์ที่ TH Sarabun New ไม่มีในข้อความ -> ใส่ในโหมดสมการ (นอกบล็อก $$ เท่านั้น)
cat > "$TMP/prep.pl" <<'PERL'
use utf8;
local $/; my $t = <STDIN>;
$t =~ s/```latex[ \t]*\n(.*?)\n```[ \t]*(?=\n|\z)/"\n\$\$\n$1\n\$\$\n"/gse;
$t =~ s{!\[([^\]]*)\]\((?:blob\/)([0-9A-Za-z-]+)\)}{
  my $f = "$ENV{IMG_DIR}/$2.png";
  (-e $f) ? "![$1]($f){width=85%}" : do { warn "ไม่พบภาพ: $f (ข้าม)\n"; "" }
}ge;
$t =~ s/√(\d+)/\\(\\sqrt{$1}\\)/g;
my %m = (
  "⌊"=>'\(\lfloor\)', "⌋"=>'\(\rfloor\)', "≈"=>'\(\approx\)', "≥"=>'\(\ge\)', "≤"=>'\(\le\)',
  "√"=>'\(\sqrt{}\)', "←"=>'\(\leftarrow\)', "→"=>'\(\rightarrow\)', "±"=>'\(\pm\)',
  "⁻¹"=>'\(^{-1}\)', "ᵀ"=>'\(^{\top}\)', "′"=>'\(^{\prime}\)',
  "α"=>'\(\alpha\)', "β"=>'\(\beta\)', "ε"=>'\(\varepsilon\)', "θ"=>'\(\theta\)', "π"=>'\(\pi\)',
  "Δ"=>'\(\Delta\)'
);
my @k = sort { length($b) <=> length($a) } keys %m;
for my $p (split /(\$\$.*?\$\$)/s, $t) {
  unless ($p =~ /^\$\$/) { for my $k (@k) { $p =~ s/\Q$k\E/$m{$k}/g } }
  print $p;
}
PERL
IMG_DIR="$IMG_DIR" perl -CSD "$TMP/prep.pl" < "$IN" > "$TMP/b.md"

# 2) ส่วนหัว LaTeX: ตัดคำไทย + ขนาดตัวอักษร
cat > "$TMP/header.tex" <<TEX
\XeTeXlinebreaklocale "th"
\XeTeXlinebreakskip=0pt plus 1pt
\AtBeginDocument{\renewcommand{\normalsize}{\fontsize{${FONT_PT}pt}{${LEAD_PT}pt}\selectfont}\normalsize}
\setlength{\parskip}{0.4em}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\usepackage{float}
\floatplacement{figure}{H}
TEX

# 3) แปลงเป็น PDF  (-raw_html: กัน <x, y> ถูกมองเป็นแท็ก HTML)
pandoc "$TMP/b.md" -f markdown-raw_html+tex_math_single_backslash -o "$OUT" \
  --pdf-engine=xelatex \
  -V documentclass=extarticle -V fontsize=14pt \
  -V geometry:a4paper,margin=20mm \
  -V mainfont="$FONT" \
  -H "$TMP/header.tex"

echo "สร้างแล้ว: $OUT"
