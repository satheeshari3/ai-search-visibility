from app.services.embedding_service import generate_embedding

print("TEST EMBEDDING FILE STARTED")



text = "this is used to convert text to vectors"

embedding = generate_embedding(text)

print("Embedding created!")
print("Type:", type(embedding))
print("Length:", len(embedding))
print("First 10 values:", embedding[:10])