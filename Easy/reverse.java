import java.util.Scanner;
public class reverse {
    public static void main(String[] agrs){
        
        
        int rem;
        int reverse = 0;

        Scanner scanner = new Scanner(System.in);
        System.out.println("Enter the number: ");
        int i = scanner.nextInt();

        while(i!=0){
            rem = i % 10;
            reverse = reverse*10+rem;
            i/=10;

        }
    System.out.printf("Reversed number: "+reverse);
    }
    
}
