import java.io.*;
import java.net.*;

public class client {
    public static void main(String[] args) throws UnknownHostException, IOException {
        Socket s = new Socket("localhost", 3035);

        DataInputStream din = new DataInputStream(s.getInputStream());
        DataOutputStream dout = new DataOutputStream(s.getOutputStream());
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        String str1 = "", str2 = "";
        while (!str1.equals("Bye")) {
            str1 = br.readLine();
            dout.writeUTF(str1);

            str2 = din.readUTF();
            System.out.println("Server says: " + str2);
        }

        s.close();
    }
}
