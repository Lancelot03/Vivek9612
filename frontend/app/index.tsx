import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Image,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Invitee {
  employeeId: string;
  employeeName: string;
  cadre: string;
  projectName: string;
}

export default function Index() {
  const [unrespondedInvitees, setUnrespondedInvitees] = useState<Invitee[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUnrespondedInvitees();
  }, []);

  const fetchUnrespondedInvitees = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/invitees/unresponded`);
      if (response.ok) {
        const data = await response.json();
        setUnrespondedInvitees(data);
      } else {
        Alert.alert('Error', 'Failed to fetch invitees');
      }
    } catch (error) {
      console.error('Error fetching invitees:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteeSelect = (invitee: Invitee) => {
    // Navigate to RSVP form with invitee data
    router.push({
      pathname: '/rsvp',
      params: {
        employeeId: invitee.employeeId,
        employeeName: invitee.employeeName,
        cadre: invitee.cadre,
        projectName: invitee.projectName,
      },
    });
  };

  const handleAdminLogin = () => {
    router.push('/admin/login');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoText}>PM Connect 3.0</Text>
            <Text style={styles.subtitle}>Event Management & Logistics</Text>
          </View>
          <TouchableOpacity style={styles.adminButton} onPress={handleAdminLogin}>
            <Text style={styles.adminButtonText}>Admin Login</Text>
          </TouchableOpacity>
        </View>

        {/* Welcome Section */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>Welcome to PM Connect 3.0!</Text>
          <Text style={styles.welcomeDescription}>
            Please select your name from the list below to proceed with your RSVP and event information.
          </Text>
        </View>

        {/* Invitee Selection */}
        <View style={styles.inviteeSection}>
          <Text style={styles.sectionTitle}>Select Your Name</Text>
          
          {unrespondedInvitees.length === 0 ? (
            <View style={styles.noInviteesContainer}>
              <Text style={styles.noInviteesText}>
                No pending invitations found. All invitees may have already responded.
              </Text>
            </View>
          ) : (
            <View style={styles.inviteeList}>
              {unrespondedInvitees.map((invitee) => (
                <TouchableOpacity
                  key={invitee.employeeId}
                  style={styles.inviteeCard}
                  onPress={() => handleInviteeSelect(invitee)}
                >
                  <View style={styles.inviteeCardContent}>
                    <Text style={styles.inviteeName}>{invitee.employeeName}</Text>
                    <Text style={styles.inviteeDetails}>
                      {invitee.cadre} • {invitee.projectName}
                    </Text>
                    <Text style={styles.inviteeId}>ID: {invitee.employeeId}</Text>
                  </View>
                  <View style={styles.arrowContainer}>
                    <Text style={styles.arrow}>→</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Information Section */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>What happens next?</Text>
          <View style={styles.infoSteps}>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>1</Text>
              </View>
              <Text style={styles.stepText}>Select your name from the list above</Text>
            </View>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>2</Text>
              </View>
              <Text style={styles.stepText}>Fill out your RSVP and logistics information</Text>
            </View>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>3</Text>
              </View>
              <Text style={styles.stepText}>Access event information, agenda, and gallery</Text>
            </View>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
        </View>
      </ScrollView>
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
  scrollContent: {
    paddingBottom: 32,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#666',
  },
  header: {
    backgroundColor: '#dc3545',
    padding: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  logoContainer: {
    flex: 1,
  },
  logoText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  adminButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  adminButtonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 14,
  },
  welcomeSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  welcomeDescription: {
    fontSize: 16,
    color: '#6c757d',
    lineHeight: 24,
  },
  inviteeSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  noInviteesContainer: {
    padding: 32,
    alignItems: 'center',
  },
  noInviteesText: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
    lineHeight: 24,
  },
  inviteeList: {
    gap: 12,
  },
  inviteeCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  inviteeCardContent: {
    flex: 1,
  },
  inviteeName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 4,
  },
  inviteeDetails: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 4,
  },
  inviteeId: {
    fontSize: 12,
    color: '#adb5bd',
  },
  arrowContainer: {
    marginLeft: 12,
  },
  arrow: {
    fontSize: 20,
    color: '#dc3545',
    fontWeight: 'bold',
  },
  infoSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  infoSteps: {
    gap: 16,
  },
  infoStep: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#007bff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  stepNumberText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  stepText: {
    flex: 1,
    fontSize: 16,
    color: '#6c757d',
    lineHeight: 24,
    marginTop: 4,
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
});