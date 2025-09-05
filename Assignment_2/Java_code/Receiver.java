import java.util.*;

public class Receiver {

    // CRC Division
    public static int[] crcDivision(int[] dividend, int[] divisor) {
        int n = divisor.length;
        int curr = n;

        int[] rem = new int[n];
        System.arraycopy(dividend, 0, rem, 0, n);

        while (curr <= dividend.length) {
            if (rem[0] == 1) {
                for (int i = 1; i < n; i++) {
                    rem[i - 1] = rem[i] ^ divisor[i];
                }
            } else {
                for (int i = 1; i < n; i++) {
                    rem[i - 1] = rem[i];
                }
            }

            if (curr < dividend.length) {
                rem[n - 1] = dividend[curr++];
            } else {
                rem = Arrays.copyOf(rem, n - 1);
                break;
            }
        }
        return rem;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        // Input Codeword
        System.out.print("Enter the number of bits in Codeword: ");
        int cwLength = sc.nextInt();
        int[] codeword = new int[cwLength];
        System.out.print("Enter the Codeword bits: ");
        for (int i = 0; i < cwLength; i++) codeword[i] = sc.nextInt();

        // Input Divisor
        System.out.print("Enter the number of bits in Divisor: ");
        int dLength = sc.nextInt();
        int[] divisor = new int[dLength];
        System.out.print("Enter the Divisor bits: ");
        for (int i = 0; i < dLength; i++) divisor[i] = sc.nextInt();

        // Perform CRC check
        int[] remainder = crcDivision(codeword, divisor);

        boolean error = false;
        for (int bit : remainder) {
            if (bit != 0) {
                error = true;
                break;
            }
        }

        if (error)
            System.out.println("Error detected in received codeword!");
        else
            System.out.println("No error detected. Codeword is valid.");

        sc.close();
    }
}
