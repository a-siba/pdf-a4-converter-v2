import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="PDF A4 Converter", layout="centered")

st.title("B4→A4 プリント変換アプリ（2段組→2ページ）")

uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"])

if uploaded_file:
    header_input = st.text_input("ヘッダー（1ページ目中央に表示）を入力してください")

    if header_input:
        # フォントパス指定と読み込み（診断付き）
        font_path = os.path.join(os.path.dirname(__file__), "NotoSansJP-Black.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"フォントファイルが見つかりません: {font_path}")
        try:
            font = ImageFont.truetype(font_path, 40)
        except Exception as e:
            raise RuntimeError(f"フォントの読み込みに失敗しました: {e}")

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

            title_size = draw1.textbbox((0, 0), header_text, font=font)
            title_width = title_size[2] - title_size[0]
            title_position = ((a4_width - title_width) // 2, 80)
            draw1.text(title_position, header_text, fill="black", font=font)

            corner_size = draw2.textbbox((0, 0), corner_label, font=font)
            right_x = a4_width - corner_size[2] - 60
            draw2.text((right_x, 40), corner_label, font=font)

            return page1, page2

        file_label = "＜解答＞" if "解答" in uploaded_file.name else "＜問題＞"
        page1, page2 = process_image(img, header_input, file_label)

        st.image(page1, caption="1ページ目（上段）", use_container_width=True)
        st.image(page2, caption="2ページ目（下段）", use_container_width=True)
