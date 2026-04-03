#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/double.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/log.h"
#include "ns3/mobility-helper.h"
#include "ns3/mobility-model.h"
#include "ns3/ssid.h"
#include "ns3/string.h"
#include "ns3/yans-wifi-channel.h"
#include "ns3/yans-wifi-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("WifiQoS_Baseline");

// 🔹 RECEIVE CALLBACK (WITH LATENCY)
void ReceivePacket(Ptr<Socket> socket)
{
    while (Ptr<Packet> packet = socket->Recv())
    {
        double now = Simulator::Now().GetSeconds();
        std::cout << "Packet received at time: " << now << std::endl;
    }
}

// 🔹 TRAFFIC GENERATOR
static void GenerateTraffic(Ptr<Socket> socket, uint32_t pktSize, uint32_t pktCount, Time pktInterval)
{
    if (pktCount > 0)
    {
        socket->Send(Create<Packet>(pktSize));
        Simulator::Schedule(pktInterval, &GenerateTraffic, socket, pktSize, pktCount - 1, pktInterval);
    }
    else
    {
        socket->Close();
    }
}

int main(int argc, char* argv[])
{
    uint32_t nSta = 10;
    uint32_t numPackets = 5;

    // 🔹 CREATE NODES
    NodeContainer staNodes;
    staNodes.Create(nSta);

    NodeContainer apNode;
    apNode.Create(1);

    // 🔹 WIFI SETUP (Wi-Fi 6 enabled)
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211ax);

    YansWifiPhyHelper phy;
    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    phy.SetChannel(channel.Create());

    WifiMacHelper mac;
    Ssid ssid = Ssid("wifi-qos");

    // STA
    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid));
    NetDeviceContainer staDevices = wifi.Install(phy, mac, staNodes);

    // AP
    mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
    NetDeviceContainer apDevice = wifi.Install(phy, mac, apNode);

    NetDeviceContainer devices;
    devices.Add(staDevices);
    devices.Add(apDevice);

    // 🔹 MOBILITY
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(staNodes);
    mobility.Install(apNode);

    // 🔹 INTERNET STACK
    InternetStackHelper internet;
    internet.Install(staNodes);
    internet.Install(apNode);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase("10.1.1.0", "255.255.255.0");

    Ipv4InterfaceContainer staInterfaces = ipv4.Assign(staDevices);
    Ipv4InterfaceContainer apInterface = ipv4.Assign(apDevice);

    // 🔹 SOCKET SETUP
    TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");

    Ptr<Socket> recvSink = Socket::CreateSocket(apNode.Get(0), tid);
    InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), 80);
    recvSink->Bind(local);
    recvSink->SetRecvCallback(MakeCallback(&ReceivePacket));

    // 🔥 MULTI-TRAFFIC WITHOUT ML (UNIFORM PRIORITY)
    for (uint32_t i = 0; i < nSta; i++)
    {
        Ptr<Socket> source = Socket::CreateSocket(staNodes.Get(i), tid);
        InetSocketAddress remote = InetSocketAddress(apInterface.GetAddress(0), 80);
        source->Connect(remote);

        uint32_t pktSize;
        int intervalMs;

        // 🔹 Traffic types (same as ML version)
        switch (i % 5)
        {
            case 0: pktSize = 200;  intervalMs = 20;   break; // VoIP
            case 1: pktSize = 1400; intervalMs = 40;   break; // Streaming
            case 2: pktSize = 1500; intervalMs = 10;   break; // File transfer
            case 3: pktSize = 800;  intervalMs = 200;  break; // Browsing
            case 4: pktSize = 300;  intervalMs = 1000; break; // Email
        }

        Time pktInterval = MilliSeconds(intervalMs);

        // ❌ NO ML → SAME PRIORITY FOR ALL
        int priority = 1;
        double startDelay = 2.0;

        std::cout << "Node " << i
                  << " | pktSize=" << pktSize
                  << " | interval=" << intervalMs
                  << " | Priority=UNIFORM" << std::endl;

        Simulator::ScheduleWithContext(source->GetNode()->GetId(),
                                       Seconds(startDelay + i * 0.1),
                                       &GenerateTraffic,
                                       source,
                                       pktSize,
                                       numPackets,
                                       pktInterval);
    }

    // 🔹 PCAP TRACE
    phy.EnablePcap("wifi-qos-baseline", devices);

    std::cout << "Running BASELINE (No ML) simulation..." << std::endl;

    Simulator::Stop(Seconds(20.0));
    Simulator::Run();
    Simulator::Destroy();

    return 0;
}
