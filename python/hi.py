queue = []
token = 0

while True:
    print("1. Generate token")
    print("2. Serve next queue")
    print("3. Display queue")
    print("4. Exit")
    
    choice = int(input("Enter your choice"))
    
    if choice == 1:
        token+= 1
        token_id = f"T{token:03d}"
        queue.append(token_id)
        print()