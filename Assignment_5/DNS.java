import java.net.InetAddress;
import java.net.UnknownHostException;

public class DNS {
    public static void main(String args[]) {
        if (args.length != 1) {
            System.err.println("Enter command line argument as an Internet Address or URL");
            System.exit(-1);
        }

        try {
            InetAddress inetAddress;

            if (Character.isDigit(args[0].charAt(0))) {
                byte[] b = new byte[4];
                String[] bytes = args[0].split("\\.");
                for (int i = 0; i < bytes.length; i++) {
                    b[i] = (byte) Integer.parseInt(bytes[i]);
                }
                inetAddress = InetAddress.getByAddress(b);
            } else {
                inetAddress = InetAddress.getByName(args[0]);
            }

            System.out.println(inetAddress.getHostName() + " / " + inetAddress.getHostAddress());

        } catch (UnknownHostException exception) {
            System.err.println("ERROR: No Internet Address for " + args[0]);
        }
    }
}
