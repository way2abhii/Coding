queue = []
token = 0
while True:
    print("1. Generate token")
    print("2. Serve next queue")
    print("3. Display queue")
    print("4. Exit")
    
    choice = int(input("Enter your choice: "))
    
    if choice == 1:
        
        token +=1
        token_id = f"T{token:03d}"
        queue.append(token_id)
        print("Token generated", token_id)
        wait_time = len(queue)*5
        print(f"Estimated time:{wait_time} minutes")  
    
    if choice == 2:
        if len(queue) == 0:
            print("No customer in queue.")
        else:
            serving = queue.pop(0)
            print("Serving", serving)      
    
    if choice == 3:
        if len(queue) ==0:
            print("empty")
        else:
            for i in range(len(queue)):
                token = queue[i]
                print(token,"*"*(i+1))
    
    if choice == 4:
        break
        
        
                   
                