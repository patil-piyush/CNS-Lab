import java.io.*;
import java.net.*;

public class server {
    public static void main(String[] args) throws IOException {
        ServerSocket ss = new ServerSocket(3035);
        System.out.println("Server started. Waiting for client...");

        Socket s = ss.accept();
        System.out.println("Client connected.");

        DataInputStream din = new DataInputStream(s.getInputStream());
        DataOutputStream dout = new DataOutputStream(s.getOutputStream());
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        String str1 = "", str2 = "";
        while (!str1.equals("Bye")) {
            str2 = din.readUTF();
            System.out.println("Client says: " + str2);

            str1 = br.readLine();
            dout.writeUTF(str1);
        }

        s.close();
        ss.close();
        System.out.println("Server closed.");
    }
}
