from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image

DOWNLOADS = Path.home() / "Downloads"
OUT = Path(r"C:\Users\chals\.openclaw\workspace\Wilo_Pump_Series_Overview.pdf")
# All supplied images share this native canvas. It becomes the page size for every page.
PAGE_W, PAGE_H = 1616, 792

PUMPS = [
    {
        "title": "Wilo-Helix VE",
        "image": "Wilo Helix VE (vertical multistage centrifugal - integrated VFD).png",
        "type": "Vertical multistage centrifugal pump dengan VFD/inverter terintegrasi.",
        "features": [
            "Konstruksi vertikal multistage untuk head tinggi pada debit kecil hingga menengah.",
            "Variable-speed drive terintegrasi untuk menjaga tekanan konstan saat demand berubah.",
            "Sesuai untuk domestic-water booster, hotel, apartemen, kantor, dan distribusi air bersih.",
            "Memerlukan pressure sensor, pressure vessel, check valve, dan proteksi low-water/dry-run sebagai bagian sistem.",
        ],
    },
    {
        "title": "Wilo-Helix FIRST V",
        "image": "Wilo Helix FIRST V (vertical multistage centrifugal).png",
        "type": "Vertical multistage centrifugal pump fixed-speed.",
        "features": [
            "Pompa vertikal multistage untuk menghasilkan head relatif tinggi.",
            "Motor fixed-speed; tidak memakai VFD terintegrasi.",
            "Cocok untuk transfer GWT ke roof tank atau booster sederhana air bersih.",
            "Untuk tekanan konstan dengan demand besar/berubah, gunakan VFD atau booster package yang sesuai.",
        ],
    },
    {
        "title": "Wilo-CronoNorm-NRG",
        "image": "Wilo CronoNorm - NRG (centrifugal horizontal end-suction, single-stage).png",
        "type": "Horizontal end-suction centrifugal pump, single-stage, long-coupled/baseplate-mounted.",
        "features": [
            "Suction axial di sisi depan dan discharge radial; konfigurasi horizontal standard.",
            "Pompa dan motor terpisah, terhubung flexible coupling pada baseplate.",
            "Umumnya mengikuti kelas dimensional EN 733 untuk utility, HVAC, dan transfer water.",
            "Cocok untuk flow menengah dengan head rendah hingga menengah; VFD/control eksternal bila perlu constant pressure.",
        ],
    },
    {
        "title": "Wilo-Atmos TERA-SCH",
        "image": "Wilo Atmos TERA - SCH (horizontal split-case centrifugal pump).png",
        "type": "Horizontal split-case centrifugal pump, single-stage, double-suction.",
        "features": [
            "Casing terbelah horizontal; rotating assembly dapat diakses tanpa membongkar pipa utama.",
            "Double-suction impeller menurunkan NPSHr dan mengurangi axial thrust.",
            "Cocok untuk debit besar pada head rendah hingga menengah.",
            "Aplikasi: main transfer/distribution, chilled water, condenser water, utilitas gedung besar, dan industri.",
        ],
    },
    {
        "title": "Wilo-Atmos GIGA-N",
        "image": "Wilo Atmos GIGA - N (horizontal end-suction centrifugal pump).png",
        "type": "Horizontal end-suction centrifugal pump, single-stage, long-coupled/baseplate-mounted.",
        "features": [
            "Pompa dan motor terpisah dengan flexible coupling dan coupling guard.",
            "Konfigurasi end-suction: suction axial dan discharge radial/top discharge.",
            "Untuk transfer water, chilled/condenser water, cooling water, dan general utility.",
            "Bukan booster package; constant pressure membutuhkan VFD dan panel kontrol eksternal.",
        ],
    },
    {
        "title": "Wilo-Medana CH1-L",
        "image": "Wilo Medana CH1-L (horizontal multistage centrifugal pump tipe close-coupled).png",
        "type": "Horizontal multistage centrifugal pump tipe close-coupled/monoblock untuk air bersih.",
        "features": [
            "Konstruksi horizontal multistage yang compact untuk head lebih tinggi.",
            "Motor dan hydraulic pump menyatu; tidak menggunakan coupling/baseplate terpisah.",
            "Fixed-speed; cocok untuk booster dan transfer kecil hingga menengah.",
            "Aplikasi: rumah besar, ruko, small commercial building, irrigation, dan utility clean water.",
        ],
    },
    {
        "title": "Wilo-Medana CH1-LC",
        "image": "Wilo-Medana CH1-LC (pompa centrifugal horizontal multistage, close-coupled atau monoblock, untuk air bersih, dengan connection flange atau coupling connection).png",
        "type": "Horizontal multistage centrifugal pump close-coupled/monoblock untuk air bersih, dengan koneksi flensa/coupling sesuai varian.",
        "features": [
            "Konsep hydraulic sama dengan Medana CH1-L: horizontal, multistage, dan compact.",
            "Koneksi flensa/coupling membantu instalasi piping yang lebih kuat dan maintenance-friendly dibanding threaded connection.",
            "Fixed-speed untuk transfer atau booster kecil hingga menengah.",
            "Pastikan kode model/datasheet lokal untuk detail material, size koneksi, dan duty range exact.",
        ],
    },
    {
        "title": "Wilo-MultiVert MVIG",
        "image": "Wilo MultiVert MVIG (vertical inline multistage centrifugal pump dengan integrated VFD).png",
        "type": "Vertical inline multistage centrifugal pump dengan VFD/inverter terintegrasi.",
        "features": [
            "Suction dan discharge inline sehingga footprint kecil dan routing pipa lebih rapi.",
            "Multistage untuk head menengah hingga tinggi; variable speed untuk operasi constant pressure.",
            "Cocok untuk booster air bersih pada rumah besar, villa, ruko, atau small commercial building.",
            "Untuk duty-standby/multi-pump tetap memerlukan manifold dan logic controller yang sesuai, atau packaged booster set.",
        ],
    },
    {
        "title": "Wilo-SCP",
        "image": "Wilo SCP (horizontal split-case centrifugal pump, single-stage, double-suction, base-mounted long-coupled).png",
        "type": "Horizontal split-case centrifugal pump, single-stage, double-suction, base-mounted long-coupled.",
        "features": [
            "Casing horizontal split memudahkan servis bearing, seal, dan impeller tanpa melepas piping utama.",
            "Double-suction impeller untuk debit besar, NPSHr lebih rendah, dan axial thrust lebih kecil.",
            "Pompa dan motor terpisah pada common baseplate, terhubung flexible coupling.",
            "Untuk main transfer/distribution, HVAC water circulation, raw water, utility, dan aplikasi flow besar.",
        ],
    },
]

GREEN = (0/255, 125/255, 76/255)
DARK = (28/255, 35/255, 33/255)
MUTED = (85/255, 96/255, 92/255)
LIGHT = (232/255, 239/255, 235/255)


def text_box(page, rect, text, size, font="helv", color=DARK, align=0, lineheight=None):
    shape = page.new_shape()
    rc = shape.insert_textbox(rect, text, fontsize=size, fontname=font, color=color, align=align, lineheight=lineheight)
    shape.commit()
    return rc


def desc_page(doc, item, index):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    # Background and visual grid.
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1), overlay=True)
    page.draw_rect(fitz.Rect(0, 0, 36, PAGE_H), color=None, fill=GREEN, overlay=True)
    page.draw_line(fitz.Point(88, 139), fitz.Point(PAGE_W - 88, 139), color=LIGHT, width=1)
    text_box(page, fitz.Rect(88, 57, PAGE_W-88, 95), f"WILO PUMP SERIES  |  {index:02d}", 16, font="hebo", color=GREEN)
    text_box(page, fitz.Rect(88, 174, PAGE_W-112, 282), item["title"], 46, font="hebo", color=DARK, lineheight=1.05)
    text_box(page, fitz.Rect(92, 317, PAGE_W-172, 390), "JENIS POMPA", 16, font="hebo", color=GREEN)
    text_box(page, fitz.Rect(92, 351, PAGE_W-150, 438), item["type"], 24, font="helv", color=DARK, lineheight=1.25)
    text_box(page, fitz.Rect(92, 481, PAGE_W-172, 518), "CIRI-CIRI UTAMA", 16, font="hebo", color=GREEN)
    # Helvetica WinAnsi encoding cannot reliably render the Unicode bullet; use ASCII hyphens.
    bullets = "\n".join(f"-  {x}" for x in item["features"])
    text_box(page, fitz.Rect(92, 530, PAGE_W-145, 715), bullets, 18, font="helv", color=MUTED, lineheight=1.42)
    text_box(page, fitz.Rect(92, 744, PAGE_W-92, 770), "Ringkasan tipe pompa untuk referensi water supply dan building services.", 12, font="helv", color=MUTED)


def image_page(doc, item):
    image_path = DOWNLOADS / item["image"]
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    # Verify source dimensions are shared, as requested.
    with Image.open(image_path) as im:
        if im.size != (PAGE_W, PAGE_H):
            raise ValueError(f"Unexpected image canvas {im.size}: {image_path.name}")
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    page.insert_image(page.rect, filename=str(image_path), keep_proportion=False, overlay=True)


def main():
    doc = fitz.open()
    doc.set_metadata({
        "title": "Wilo Pump Series Overview",
        "author": "OpenClaw",
        "subject": "Pump types and key characteristics",
        "keywords": "Wilo, pump, water supply, building services",
    })
    for n, item in enumerate(PUMPS, 1):
        desc_page(doc, item, n)
        image_page(doc, item)
    doc.save(OUT, garbage=4, deflate=True)
    doc.close()
    print(OUT)

if __name__ == "__main__":
    main()
