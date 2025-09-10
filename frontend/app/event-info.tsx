import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Agenda {
  agendaId: string;
  agendaTitle: string;
  pdfBase64: string;
  uploadTimestamp: string;
}

interface CabAllocation {
  cabId: string;
  cabNumber: number;
  assignedMembers: string[];
  pickupLocation: string;
  pickupTime: string;
}

export default function EventInfo() {
  const params = useLocalSearchParams();
  const { employeeId } = params;

  const [currentTab, setCurrentTab] = useState('agenda');
  const [agenda, setAgenda] = useState<Agenda | null>(null);
  const [cabAllocation, setCabAllocation] = useState<CabAllocation | null>(null);
  const [loading, setLoading] = useState(true);
  const [pdfModalVisible, setPdfModalVisible] = useState(false);

  useEffect(() => {
    fetchEventData();
  }, []);

  const fetchEventData = async () => {
    setLoading(true);
    try {
      // Fetch agenda
      const agendaResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agenda`);
      if (agendaResponse.ok) {
        const agendaData = await agendaResponse.json();
        if (agendaData.agendaId) {
          setAgenda(agendaData);
        }
      }

      // Fetch cab allocation
      const cabResponse = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/cab-allocations/${employeeId}`);
      if (cabResponse.ok) {
        const cabData = await cabResponse.json();
        if (cabData.cabId) {
          setCabAllocation(cabData);
        }
      }
    } catch (error) {
      console.error('Error fetching event data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAgenda = () => {
    if (agenda) {
      Alert.alert(
        'Download Agenda',
        'Agenda PDF is ready to view',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'View PDF', onPress: () => setPdfModalVisible(true) },
        ]
      );
    }
  };

  const navigateToGallery = () => {
    router.push({
      pathname: '/gallery',
      params: { employeeId: employeeId as string },
    });
  };

  const renderAgendaTab = () => (
    <View style={styles.tabContent}>
      {agenda ? (
        <View style={styles.agendaCard}>
          <Text style={styles.agendaTitle}>{agenda.agendaTitle}</Text>
          <Text style={styles.agendaDate}>
            Uploaded: {new Date(agenda.uploadTimestamp).toLocaleDateString()}
          </Text>
          <TouchableOpacity style={styles.downloadButton} onPress={handleDownloadAgenda}>
            <Text style={styles.downloadButtonText}>📄 View Agenda PDF</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.noDataCard}>
          <Text style={styles.noDataText}>📋 No agenda available yet</Text>
          <Text style={styles.noDataSubtext}>The event agenda will be uploaded soon</Text>
        </View>
      )}
    </View>
  );

  const renderCabTab = () => (
    <View style={styles.tabContent}>
      {cabAllocation ? (
        <View style={styles.cabCard}>
          <Text style={styles.cabTitle}>🚗 Your Cab Details</Text>
          <View style={styles.cabDetails}>
            <View style={styles.cabDetailRow}>
              <Text style={styles.cabDetailLabel}>Cab Number:</Text>
              <Text style={styles.cabDetailValue}>{cabAllocation.cabNumber}</Text>
            </View>
            <View style={styles.cabDetailRow}>
              <Text style={styles.cabDetailLabel}>Pickup Location:</Text>
              <Text style={styles.cabDetailValue}>{cabAllocation.pickupLocation}</Text>
            </View>
            <View style={styles.cabDetailRow}>
              <Text style={styles.cabDetailLabel}>Pickup Time:</Text>
              <Text style={styles.cabDetailValue}>{cabAllocation.pickupTime}</Text>
            </View>
          </View>
          
          <Text style={styles.fellowPassengersTitle}>Fellow Passengers:</Text>
          <View style={styles.fellowPassengersList}>
            {cabAllocation.assignedMembers
              .filter(memberId => memberId !== employeeId)
              .map((memberId, index) => (
                <View key={index} style={styles.fellowPassengerItem}>
                  <Text style={styles.fellowPassengerText}>👤 Employee ID: {memberId}</Text>
                </View>
              ))}
          </View>
        </View>
      ) : (
        <View style={styles.noDataCard}>
          <Text style={styles.noDataText}>🚗 No cab allocation yet</Text>
          <Text style={styles.noDataSubtext}>Cab details will be assigned closer to the event</Text>
        </View>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#dc3545" />
          <Text style={styles.loadingText}>Loading event information...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Event Information</Text>
          <Text style={styles.headerSubtitle}>PM Connect 3.0</Text>
        </View>

        {/* Welcome Message */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeText}>
            🎉 Thank you for your RSVP! Here's your event information and updates.
          </Text>
        </View>

        {/* Tab Navigation */}
        <View style={styles.tabNavigation}>
          <TouchableOpacity
            style={[styles.tab, currentTab === 'agenda' && styles.activeTab]}
            onPress={() => setCurrentTab('agenda')}
          >
            <Text style={[styles.tabText, currentTab === 'agenda' && styles.activeTabText]}>
              📋 Agenda
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, currentTab === 'cab' && styles.activeTab]}
            onPress={() => setCurrentTab('cab')}
          >
            <Text style={[styles.tabText, currentTab === 'cab' && styles.activeTabText]}>
              🚗 Cab Details
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        {currentTab === 'agenda' && renderAgendaTab()}
        {currentTab === 'cab' && renderCabTab()}

        {/* Gallery Section */}
        <View style={styles.gallerySection}>
          <Text style={styles.gallerySectionTitle}>📸 Event Gallery</Text>
          <Text style={styles.gallerySectionDescription}>
            View photos from previous PM Connect events and upload your own memories!
          </Text>
          <TouchableOpacity style={styles.galleryButton} onPress={navigateToGallery}>
            <Text style={styles.galleryButtonText}>Explore Gallery</Text>
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
        </View>
      </ScrollView>

      {/* PDF Modal */}
      <Modal
        visible={pdfModalVisible}
        animationType="slide"
        onRequestClose={() => setPdfModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Event Agenda</Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setPdfModalVisible(false)}
            >
              <Text style={styles.modalCloseText}>✕ Close</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.modalContent}>
            <Text style={styles.pdfPlaceholder}>
              📄 PDF Viewer would be implemented here{'\n'}
              In a production app, you would use react-native-pdf or similar library
            </Text>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#6c757d',
    marginTop: 16,
  },
  header: {
    backgroundColor: '#dc3545',
    padding: 24,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    marginTop: 4,
  },
  welcomeSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  welcomeText: {
    fontSize: 16,
    color: '#28a745',
    textAlign: 'center',
    lineHeight: 24,
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: 'white',
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    padding: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#dc3545',
  },
  tabText: {
    fontSize: 16,
    color: '#6c757d',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#dc3545',
    fontWeight: 'bold',
  },
  tabContent: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  agendaCard: {
    padding: 20,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  agendaTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  agendaDate: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 16,
  },
  downloadButton: {
    backgroundColor: '#007bff',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  downloadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  cabCard: {
    padding: 20,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  cabTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  cabDetails: {
    marginBottom: 20,
  },
  cabDetailRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  cabDetailLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6c757d',
    width: 120,
  },
  cabDetailValue: {
    fontSize: 14,
    color: '#2c3e50',
    flex: 1,
  },
  fellowPassengersTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  fellowPassengersList: {
    gap: 8,
  },
  fellowPassengerItem: {
    padding: 8,
    backgroundColor: 'white',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  fellowPassengerText: {
    fontSize: 14,
    color: '#495057',
  },
  noDataCard: {
    padding: 32,
    alignItems: 'center',
  },
  noDataText: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 8,
    textAlign: 'center',
  },
  noDataSubtext: {
    fontSize: 14,
    color: '#adb5bd',
    textAlign: 'center',
  },
  gallerySection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  gallerySectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  gallerySectionDescription: {
    fontSize: 16,
    color: '#6c757d',
    lineHeight: 24,
    marginBottom: 16,
  },
  galleryButton: {
    backgroundColor: '#28a745',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  galleryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  modalCloseButton: {
    padding: 8,
  },
  modalCloseText: {
    color: '#dc3545',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  pdfPlaceholder: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
    lineHeight: 24,
  },
});