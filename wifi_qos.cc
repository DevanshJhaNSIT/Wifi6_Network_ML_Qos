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

NS_LOG_COMPONENT_DEFINE("WifiQoS");

void ReceivePacket(Ptr<Socket> socket)
{
    while (socket->Recv())
    {
        std::cout << "Received one packet!" << std::endl;
    }
}

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
    uint32_t packetSize = 1000;
    uint32_t numPackets = 5;
    Time interval = Seconds(1.0);

    // 🔹 CREATE NODES
    NodeContainer staNodes;
    staNodes.Create(nSta);

    NodeContainer apNode;
    apNode.Create(1);

    // 🔹 WIFI SETUP
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

    // 🔹 RECEIVE SOCKET ON AP
    TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");

    Ptr<Socket> recvSink = Socket::CreateSocket(apNode.Get(0), tid);
    InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), 80);
    recvSink->Bind(local);
    recvSink->SetRecvCallback(MakeCallback(&ReceivePacket));

    // 🔥 MULTIPLE STATIONS SEND TRAFFIC
    for (uint32_t i = 0; i < nSta; i++)
{
    Ptr<Socket> source = Socket::CreateSocket(staNodes.Get(i), tid);
    InetSocketAddress remote = InetSocketAddress(apInterface.GetAddress(0), 80);
    source->Connect(remote);

    // 🔥 Assign traffic type
    std::string trafficType;
    uint32_t pktSize;
    Time pktInterval;

    if (i % 3 == 0)
    {
        trafficType = "VoIP";
        pktSize = 200;
        pktInterval = MilliSeconds(20);
    }
    else if (i % 3 == 1)
    {
        trafficType = "Video";
        pktSize = 1200;
        pktInterval = MilliSeconds(50);
    }
    else
    {
        trafficType = "HTTP";
        pktSize = 800;
        pktInterval = MilliSeconds(200);
    }

    std::cout << "Node " << i << " Traffic: " << trafficType << std::endl;

    Simulator::ScheduleWithContext(source->GetNode()->GetId(),
                                   Seconds(1.0 + i * 0.1),
                                   &GenerateTraffic,
                                   source,
                                   pktSize,
                                   numPackets,
                                   pktInterval);
}

    // 🔹 PCAP TRACE
    phy.EnablePcap("wifi-qos", devices);

    std::cout << "Running Wi-Fi QoS simulation with " << nSta << " stations..." << std::endl;

    Simulator::Stop(Seconds(20.0));
    Simulator::Run();
    Simulator::Destroy();

    return 0;
}

