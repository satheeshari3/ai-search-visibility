

def chunk_text(text, chunk_size, overlap):
    chunk_list = []
    words = text.split()
    start = 0
    while start < len(words):
        end = start+chunk_size
        chunk =" ".join(words[start:end])
        chunk_list.append(chunk)
        start = start+chunk_size - overlap

    return chunk_list
    
        

