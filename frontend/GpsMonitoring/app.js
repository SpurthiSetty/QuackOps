// app.js
import express from "express";
import { createServer } from "http";
import { Server as SocketServer } from "socket.io";
import dgram from "dgram";
import { parseNmeaSentence } from "nmea-simple";

const UDP_PORT = 11123;
const HTTP_PORT = 3000;

const app = express();
const httpServer = createServer(app);
const io = new SocketServer(httpServer);
app.use(express.static("public"));

// Create UDP socket to receive GPS2IP data
const udpServer = dgram.createSocket("udp4");

udpServer.on("listening", () => {
  console.log(`Listening for GPS data on UDP port ${UDP_PORT}...`);
});

udpServer.on("message", (msg, rinfo) => {
  const line = msg.toString().trim();
  try {
    const parsed = parseNmeaSentence(line);

    if (parsed.sentenceId === "RMC" || parsed.sentenceId === "GGA") {
      const data = {
        type: parsed.sentenceId,
        lat: parsed.latitude ?? parsed.lat,
        lon: parsed.longitude ?? parsed.lon,
        alt: parsed.altitude ?? parsed.alt ?? null,
        time: parsed.time ?? new Date().toISOString(),
      };
      console.log("Parsed GPS:", data);
      io.emit("gps", data);
    }
  } catch (err) {
    // Ignore lines that aren't valid NMEA
  }
});

udpServer.bind(UDP_PORT);

// WebSocket connection to clients
io.on("connection", (socket) => {
  console.log("Browser connected");
});

httpServer.listen(HTTP_PORT, () =>
  console.log(`Web server running at http://localhost:${HTTP_PORT}`)
);
