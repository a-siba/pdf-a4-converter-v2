import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import os
import re
from io import BytesIO

st.set_page_config(page_title="PDF A4 Converter", layout="centered")

st.title("B4→A4 プリント変換アプリ（2段組→2ページ）")

uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"])

if uploaded_file:

    # フォントパス指定と読み込み（診断付き）
    font_path = os.path.join(os.path.dirname(__file__), "NotoSansJP-Black.ttf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"フォントファイルが見つかりません: {font_path}")
    try:
        font = ImageFont.truetype(font_path, 40)
    except Exception as e:
        raise RuntimeError(f"フォントの読み込みに失敗しました: {e}")

    # ファイル名からタイトル部分を抽出
    filename = os.path.splitext(uploaded_file.name)[0]
    match = re.search(r"定期テスト直前対策_[^_]+_[^_]+_([^_]+)_([^_]+)_(.+)", filename)
    if match:
        unit1, unit2, label_raw = match.groups()
        unit_combined = f"{unit1}，{unit2}"
        header_text = f"{unit_combined}＜{label_raw}＞"
    else:
        header_text = "＜問題＞"

    # PDFを画像に変換
    pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = pdf_doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def process_image(img, header_text, corner_label):
        w, h = img.size
        mid_y = h // 2
        upper = img.crop((0, 0, w, mid_y))
        lower = img.crop((0, mid_y, w, h))

        a4_width, a4_height = 2480, 3508  # A4 @ 300dpi
        page1 = Image.new("RGB", (a4_width, a4_height), "white")
        page2 = Image.new("RGB", (a4_width, a4_height), "white")

        upper_resized = upper.resize((a4_width - 200, a4_height - 400))
        lower_resized = lower.resize((a4_width - 200, a4_height - 400))

        page1.paste(upper_resized, (100, 200))
        page2.paste(lower_resized, (100, 200))

        draw1 = ImageDraw.Draw(page1)
        draw2 = ImageDraw.Draw(page2)

        # ヘッダーを2ページ目の右上に表示
        corner_size2 = draw2.textbbox((0, 0), header_text, font=font)
        right_x2 = a4_width - corner_size2[2] - 60
        draw2.text((right_x2, 40), header_text, font=font)

        # ＜問題＞ or ＜解答＞ を右上に追加
        label_size = draw2.textbbox((0, 0), corner_label, font=font)
        right_x_label = a4_width - label_size[2] - 60
        draw2.text((right_x_label, 100), corner_label, font=font)

        return page1, page2

    file_label = "＜解答＞" if "解答" in uploaded_file.name else "＜問題＞"
    page1, page2 = process_image(img, header_text, file_label)

    # PDFとして保存
    output_pdf = BytesIO()
    page1.save(output_pdf, "PDF", resolution=300, save_all=True, append_images=[page2])
    output_pdf.seek(0)

    st.download_button(
        label="📄 加工済みPDFをダウンロード",
        data=output_pdf,
        file_name="converted.pdf",
        mime="application/pdf"
    )

    st.success("2ページに分割されたPDFが生成されました。")
