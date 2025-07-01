
import streamlit as st
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import tempfile
import io
import os

def extract_header_text(pdf_file):
    reader = PdfReader(pdf_file)
    first_page = reader.pages[0]
    text = first_page.extract_text()
    if text:
        lines = text.strip().split('\n')
        for line in lines:
            if "定期テスト直前対策パーフェクト" in line:
                parts = line.replace('\t', '　').split('　')  # 全角スペースで分割
                for i, part in enumerate(parts):
                    if "定期テスト直前対策パーフェクト" in part and i + 1 < len(parts):
                        return parts[i + 1].strip()
        return lines[0]  # fallback
    return ""

def pdf_to_image(pdf_file):
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return img

def process_image(img, header_text):
    width, height = img.size
    midpoint = width // 2
    header_height = 380

    header = img.crop((0, 0, width, header_height))
    content1 = img.crop((0, header_height, midpoint, height))
    content2 = img.crop((midpoint, header_height, width, height))

    a4_width, a4_height = 2480, 3508
    a4_page1 = Image.new("RGB", (a4_width, a4_height), "white")
    a4_page2 = Image.new("RGB", (a4_width, a4_height), "white")

    header_aspect = header.width / header.height
    header_target_height = int(a4_width / header_aspect)
    header_resized = header.resize((a4_width, header_target_height))
    a4_page1.paste(header_resized, (0, 0))

    content1_aspect = content1.width / content1.height
    content1_target_height = a4_height - header_target_height
    content1_target_width = int(content1_target_height * content1_aspect)
    content1_resized = content1.resize((content1_target_width, content1_target_height))
    a4_page1.paste(content1_resized, (0, header_target_height))

    title_margin_top = 120
    content2_aspect = content2.width / content2.height
    content2_target_height = a4_height - title_margin_top
    content2_target_width = int(content2_target_height * content2_aspect)
    content2_resized = content2.resize((content2_target_width, content2_target_height))
    a4_page2.paste(content2_resized, (0, title_margin_top))

    draw1 = ImageDraw.Draw(a4_page1)
    mid_x = a4_width // 2
    draw1.rectangle([mid_x - 10, header_target_height, mid_x + 10, a4_height], fill="white")

    draw2 = ImageDraw.Draw(a4_page2)
    draw2.rectangle([0, 0, 4, a4_height], fill="white")

    font_path = "NotoSansJP-Black.ttf"
    font = ImageFont.truetype(font_path, 40)

    title_bbox = draw2.textbbox((0, 0), header_text, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_position = (a4_width - title_width - 60, 40)
    draw2.text(title_position, header_text, fill="black", font=font)

    return a4_page1, a4_page2

st.title("B4プリント → A4加工ツール（縦線除去・右肩タイトル抽出）")
uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type="pdf")

if uploaded_file:
    header_candidate = extract_header_text(uploaded_file)
    st.write("### 自動抽出されたタイトル（編集可能）")
    header_input = st.text_input("タイトル文言", value=header_candidate)

    uploaded_file.seek(0)
    img = pdf_to_image(uploaded_file)
    page1, page2 = process_image(img, header_input)

    st.image(page1, caption="A4ページ1（ヘッダーあり）", use_container_width=True)
    st.image(page2, caption="A4ページ2（右肩タイトル付き）", use_container_width=True)

    pdf_bytes = io.BytesIO()
    page1.save(pdf_bytes, format="PDF", save_all=True, append_images=[page2])
    st.download_button("加工済PDFをダウンロード", data=pdf_bytes.getvalue(), file_name="converted.pdf", mime="application/pdf")
