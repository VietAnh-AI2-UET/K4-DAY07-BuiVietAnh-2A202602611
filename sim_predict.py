from src.embeddings import _mock_embed
from src.chunking import compute_similarity

pairs = [
    ("Mèo thích ăn cá.", "Chó thích gặm xương."),
    ("Làm sao để đăng ký bán hàng trên Shopee?", "Hướng dẫn mở gian hàng trên Shopee."),
    ("Tốc độ ánh sáng rất nhanh.", "Vận tốc của ánh sáng lớn lắm."),
    ("Giá cổ phiếu đang tăng mạnh.", "Thời tiết hôm nay rất đẹp."),
    ("Tôi thích học Python.", "Python là ngôn ngữ lập trình tôi yêu thích.")
]

for a, b in pairs:
    vec_a = _mock_embed(a)
    vec_b = _mock_embed(b)
    sim = compute_similarity(vec_a, vec_b)
    print(f'"{a}" vs "{b}" -> Sim: {sim:.4f}')
