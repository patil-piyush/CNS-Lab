import java.util.*;

public class Sender {

    // Function to perform CRC Division
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
                rem = Arrays.copyOf(rem, n - 1); // pop last
                break;
            }
        }
        return rem;
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        // Input Dataword
        System.out.print("Enter the number of bits in Dataword (7 or 8 for ASCII): ");
        int dwLength = sc.nextInt();
        int[] dataword = new int[dwLength];
        System.out.print("Enter the Dataword bits: ");
        for (int i = 0; i < dwLength; i++) dataword[i] = sc.nextInt();

        // Input Divisor
        System.out.print("Enter the number of bits in Divisor: ");
        int dLength = sc.nextInt();
        int[] divisor = new int[dLength];
        System.out.print("Enter the Divisor bits: ");
        for (int i = 0; i < dLength; i++) divisor[i] = sc.nextInt();

        // Create Dividend = Dataword + (dLength - 1) zeros
        int[] dividend = new int[dwLength + dLength - 1];
        for (int i = 0; i < dwLength; i++) dividend[i] = dataword[i];

        // Compute remainder
        int[] remainder = crcDivision(dividend, divisor);

        // Codeword = Dataword + Remainder
        int[] codeword = new int[dwLength + remainder.length];
        System.arraycopy(dataword, 0, codeword, 0, dwLength);
        System.arraycopy(remainder, 0, codeword, dwLength, remainder.length);

        // Output
        System.out.print("Remainder (CRC bits): ");
        for (int bit : remainder) System.out.print(bit);
        System.out.println();

        System.out.print("Codeword to be transmitted: ");
        for (int bit : codeword) System.out.print(bit);
        System.out.println();

        sc.close();
    }
}
