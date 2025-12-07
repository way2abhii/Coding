
            print("empty")
        else:
            for i in range(len(queue)):
                token = queue[i]
                print(token,"*"*(i+1))
    
    if choice == 4:
        wait_time = len(queue)*5