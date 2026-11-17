def stream_generator(resp, chunk_size=8192):
    for chunk in resp.iter_content(chunk_size=chunk_size):
        if chunk:
            yield chunk
