import java.io.*;
import java.net.*;
import java.util.Scanner;

public class SimpleClient {
    public static void main(String[] args) {
        try (Socket socket = new Socket("localhost", 2200);
             DataOutputStream dos = new DataOutputStream(socket.getOutputStream());
             DataInputStream dis = new DataInputStream(socket.getInputStream());
             Scanner scanner = new Scanner(System.in)) {

            System.out.println("Connected to server!");

            System.out.print("Enter number of packets to send: ");
            int totalPackets = scanner.nextInt();
            System.out.print("Enter window size: ");
            int windowSize = scanner.nextInt();

            // send total packets + window size to server
            dos.writeInt(totalPackets);
            dos.writeInt(windowSize);
            dos.flush();

            int base = 0;
            while (base < totalPackets) {
                int end = Math.min(base + windowSize, totalPackets);

                // Send window of packets
                for (int i = base; i < end; i++) {
                    dos.writeUTF(Integer.toString(i));
                    System.out.println("Sent packet: " + i);
                }
                dos.flush();

                // Receive ACK for the window
                int ack = dis.readInt();
                if (ack == -1) {
                    // Go-Back-N retransmission
                    System.out.println("ACK missing! Resending from packet " + base);
                } else {
                    System.out.println("Received ACK for packet " + ack);
                    base = ack + 1; // Move window
                }
            }

            System.out.println("All packets transmitted successfully.");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
