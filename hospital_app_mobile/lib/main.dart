import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(const PharmaShieldHospitalApp());
}

class PharmaShieldHospitalApp extends StatelessWidget {
  const PharmaShieldHospitalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PharmaShield Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0E1117),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF2DD4BF),
          surface: Color(0xFF1A1D23),
        ),
      ),
      home: const MainMobileNavigationScreen(),
    );
  }
}

class MainMobileNavigationScreen extends StatefulWidget {
  const MainMobileNavigationScreen({super.key});

  @override
  State<MainMobileNavigationScreen> createState() => _MainMobileNavigationScreenState();
}

class _MainMobileNavigationScreenState extends State<MainMobileNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HospitalMonitorTab(),
    const SapStoManagerTab(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (idx) => setState(() => _currentIndex = idx),
        backgroundColor: const Color(0xFF111418),
        selectedItemColor: const Color(0xFF2DD4BF),
        unselectedItemColor: const Color(0xFF9CA3AF),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.local_hospital), label: 'Hospital'),
          BottomNavigationBarItem(icon: Icon(Icons.inventory), label: 'SAP STO'),
        ],
      ),
    );
  }
}

class HospitalMonitorTab extends StatefulWidget {
  const HospitalMonitorTab({super.key});

  @override
  State<HospitalMonitorTab> createState() => _HospitalMonitorTabState();
}

class _HospitalMonitorTabState extends State<HospitalMonitorTab> {
  Map<String, dynamic> _status = {};
  bool _isLoading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchStatus();
    _timer = Timer.periodic(const Duration(seconds: 2), (_) => _fetchStatus());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchStatus() async {
    try {
      final response = await http
          .get(Uri.parse('http://127.0.0.1:5002/api/hospital/shipment-status'))
          .timeout(const Duration(seconds: 2));

      if (response.statusCode == 200) {
        setState(() {
          _status = json.decode(response.body);
          _isLoading = false;
        });
      }
    } catch (_) {}
  }

  Color _getRiskColor(String risk) {
    switch (risk.toUpperCase()) {
      case 'SAFE':
        return const Color(0xFF22C55E);
      case 'WARNING':
        return const Color(0xFFF59E0B);
      case 'CRITICAL':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF64748B);
    }
  }

  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri launchUri = Uri(scheme: 'tel', path: phoneNumber);
    if (await canLaunchUrl(launchUri)) {
      await launchUrl(launchUri);
    }
  }

  @override
  Widget build(BuildContext context) {
    final riskLvl = _status['rule_based_risk_level'] ?? 'SAFE';
    final riskColor = _getRiskColor(riskLvl);
    final temp = _status['temperature']?.toString() ?? '5.0';
    final humidity = _status['humidity']?.toString() ?? '45.0';
    final tts = _status['tts_remaining_hours']?.toString() ?? '72.0';
    final pct = _status['percent_remaining']?.toString() ?? '100';

    final contacts = _status['contacts']?['personnel'] ?? {};
    final driverName = contacts['driver']?['name'] ?? 'VAIBHAV';
    final driverPhone = contacts['driver']?['phone'] ?? '+91 75004 94102';
    final managerName = contacts['delivery_manager']?['name'] ?? 'VAISHNAVI';
    final managerPhone = contacts['delivery_manager']?['phone'] ?? '+91 8057882151';

    final bool isWarning = riskLvl == 'WARNING';
    final bool isCritical = riskLvl == 'CRITICAL' || riskLvl == 'SPOILED';
    final bool rerouted = _status['rerouted'] == true;
    final recoveryHub = _status['recovery_hub'];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF111418),
        title: const Row(
          children: [
            Icon(Icons.local_hospital, color: Color(0xFF2DD4BF)),
            SizedBox(width: 8),
            Text('PharmaShield Hospital', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2DD4BF)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (isWarning)
                    Container(
                      padding: const EdgeInsets.all(14),
                      margin: const EdgeInsets.only(bottom: 14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF59E0B).withOpacity(0.2),
                        border: Border.all(color: const Color(0xFFF59E0B), width: 2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        '⚠️ EARLY WARNING: Cold-chain excursion detected!',
                        style: TextStyle(color: Color(0xFFF59E0B), fontWeight: FontWeight.bold, fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  if (isCritical)
                    Container(
                      padding: const EdgeInsets.all(14),
                      margin: const EdgeInsets.only(bottom: 14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEF4444).withOpacity(0.25),
                        border: Border.all(color: const Color(0xFFEF4444), width: 2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        '🚨 CRITICAL BREACH: Temperature outside safe zone!',
                        style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.bold, fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                    ),

                  Card(
                    color: const Color(0xFF1A1D23),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: const BorderSide(color: Color(0xFF2A2E37)),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('LIVE SHIPMENT STATUS', style: TextStyle(color: Color(0xFF9CA3AF), fontSize: 12, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 12),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                decoration: BoxDecoration(
                                  color: riskColor.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(color: riskColor),
                                ),
                                child: Text(riskLvl, style: TextStyle(color: riskColor, fontWeight: FontWeight.bold, fontSize: 14)),
                              ),
                              Text('$tts hrs', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF2DD4BF))),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(child: _buildMetricTile('Temperature', '$temp °C')),
                              const SizedBox(width: 8),
                              Expanded(child: _buildMetricTile('Humidity', '$humidity %')),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(child: _buildMetricTile('Shelf Life Left', '$pct %')),
                              const SizedBox(width: 8),
                              Expanded(child: _buildMetricTile('Shipment ID', 'SHP-9942')),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  if (rerouted && recoveryHub != null) ...[
                    Card(
                      color: const Color(0xFF1A1D23),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: const BorderSide(color: Color(0xFF2DD4BF)),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('🔀 COLD-HUB REROUTING & SAP STO ACTIVE', style: TextStyle(color: Color(0xFFF59E0B), fontSize: 12, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 8),
                            Text(recoveryHub['name'] ?? 'Recovery Hub', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                            const SizedBox(height: 4),
                            Text('Cap: ${recoveryHub['current_load']}/${recoveryHub['capacity']} • Status: In Transit', style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 13)),
                            const SizedBox(height: 8),
                            const Text('📦 SAP STO Dispatched: #STO-1000 (CONFIRMED)', style: TextStyle(color: Color(0xFF2DD4BF), fontWeight: FontWeight.bold, fontSize: 12)),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  Card(
                    color: const Color(0xFF1A1D23),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: const BorderSide(color: Color(0xFF2A2E37)),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('KEY PERSONNEL CONTACTS', style: TextStyle(color: Color(0xFF9CA3AF), fontSize: 12, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 12),
                          _buildContactRow('Driver', driverName, driverPhone),
                          const Divider(color: Color(0xFF2A2E37)),
                          _buildContactRow('Manager', managerName, managerPhone),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildMetricTile(String label, String value) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF111418),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF2A2E37)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 11)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildContactRow(String role, String name, String phone) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
            Text(role, style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 12)),
          ],
        ),
        ElevatedButton.icon(
          onPressed: () => _makePhoneCall(phone),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF2DD4BF),
            foregroundColor: const Color(0xFF0E1117),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          icon: const Icon(Icons.phone, size: 16),
          label: const Text('Call', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}

class SapStoManagerTab extends StatefulWidget {
  const SapStoManagerTab({super.key});

  @override
  State<SapStoManagerTab> createState() => _SapStoManagerTabState();
}

class _SapStoManagerTabState extends State<SapStoManagerTab> {
  List<dynamic> _orders = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchOrders();
  }

  Future<void> _fetchOrders() async {
    try {
      final res = await http.get(Uri.parse('http://127.0.0.1:5000/api/sap/orders'));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        setState(() {
          _orders = (data['orders'] as List).reversed.toList();
          _isLoading = false;
        });
      }
    } catch (_) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _dispatchEmergencySTO() async {
    try {
      final res = await http.post(
        Uri.parse('http://127.0.0.1:5000/api/sap/stock-transport-order'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'shipment_id': 'SHP-9942',
          'origin_hub': 'Origin Transit MH-12',
          'destination_hub': 'Panvel Cold Hub',
          'reason': 'EMERGENCY_MANUAL_DISPATCH',
          'tts_remaining_hours': 1.5,
          'risk_level': 'CRITICAL',
          'distance_km': 8.4
        }),
      );
      if (res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ SAP STO Order Created & Dispatched!')),
        );
        _fetchOrders();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error connecting to SAP mock server on port 5000')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF111418),
        title: const Row(
          children: [
            Icon(Icons.inventory, color: Color(0xFF2DD4BF)),
            SizedBox(width: 8),
            Text('SAP STO Orders', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ElevatedButton.icon(
              onPressed: _dispatchEmergencySTO,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2DD4BF),
                foregroundColor: const Color(0xFF0E1117),
                padding: const EdgeInsets.all(14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              icon: const Icon(Icons.flash_on),
              label: const Text('Dispatch Manual Emergency STO', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            ),
            const SizedBox(height: 16),
            const Text('ORDER LOG HISTORY', style: TextStyle(color: Color(0xFF9CA3AF), fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            if (_isLoading)
              const Center(child: CircularProgressIndicator(color: Color(0xFF2DD4BF)))
            else if (_orders.isEmpty)
              const Padding(
                padding: EdgeInsets.all(20.0),
                child: Text('No STO orders dispatched yet.\nTrigger a cooling failure scenario to auto-generate STOs.', textAlign: TextAlign.center, style: TextStyle(color: Color(0xFF9CA3AF))),
              )
            else
              ..._orders.map((sto) => Card(
                    color: const Color(0xFF111418),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10), side: const BorderSide(color: Color(0xFF2A2E37))),
                    margin: const EdgeInsets.only(bottom: 10),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('📦 ${sto['order_number']}', style: const TextStyle(color: Color(0xFF2DD4BF), fontWeight: FontWeight.bold, fontSize: 16)),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(color: const Color(0xFF22C55E).withOpacity(0.2), borderRadius: BorderRadius.circular(6)),
                                child: Text(sto['status'], style: const TextStyle(color: Color(0xFF22C55E), fontSize: 11, fontWeight: FontWeight.bold)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text('Shipment: ${sto['shipment_id']} • Reason: ${sto['reason']}', style: const TextStyle(color: Colors.white, fontSize: 13)),
                          Text('From: ${sto['origin_hub']} → To: ${sto['destination_hub']}', style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 12)),
                        ],
                      ),
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}
