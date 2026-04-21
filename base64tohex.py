import base64

frames = [
    #Insert your base64-encoded frames here
]


for i, s in enumerate(frames, 1):
    b = base64.b64decode(s)
    hex_str = " ".join(f"{x:02x}" for x in b)
    print(hex_str)
    print()