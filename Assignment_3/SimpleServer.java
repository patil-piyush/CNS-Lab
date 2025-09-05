import java.io.*;
import java.net.*;

public class SimpleServer {
    public static void main(String args[]) throws IOException {
        ServerSocket server = new ServerSocket(2200);
        System.out.println("Waiting for client connection...");
        Socket socket = server.accept();
        System.out.println("Client connected: " + socket.getInetAddress());

        DataOutputStream dos = new DataOutputStream(socket.getOutputStream());
        DataInputStream dis = new DataInputStream(socket.getInputStream());

        try {
            int totalPackets = dis.readInt();
            int windowSize = dis.readInt();

            System.out.println("Expecting " + totalPackets + " packets with window size " + windowSize);

            int expected = 0;
            while (expected < totalPackets) {
                for (int i = 0; i < windowSize && expected < totalPackets; i++) {
                    String pkt = dis.readUTF();
                    int seq = Integer.parseInt(pkt);
                    System.out.println("Received packet: " + seq);

                    // Simulate packet loss (optional)
                    if (Math.random() < 0.2) { // 20% chance
                        System.out.println("Simulated loss of packet " + seq);
                        dos.writeInt(-1); // tell client to retransmit from base
                        dos.flush();
                        break;
                    }

                    if (seq == expected) {
                        expected++;
                    }
                }

                // Send ACK
                dos.writeInt(expected - 1);
                dos.flush();
                System.out.println("Sent ACK for packet " + (expected - 1));
            }

            System.out.println("All packets received successfully.");
        } catch (EOFException e) {
            System.out.println("Client closed connection.");
        } finally {
            dos.close();
            dis.close();
            socket.close();
            server.close();
        }
    }
}
