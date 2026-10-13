from app.services.chunker import chunk_text

text = " ".join([f"word{i}" for i in range(120)])

chunks = chunk_text(text, 50, 10)
print("Number of chunks:", len(chunks))

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(chunk)