import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
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

  const { 
    user, 
    isAuthenticated, 
    isLoading: authLoading, 
    isAdmin, 
    isFirstLogin, 
    mustChangePassword 
  } = useAuth();

  useEffect(() => {
    handleAuthRedirects();
  }, [isAuthenticated, user, authLoading]);

  useEffect(() => {
    if (!authLoading) {
      fetchUnrespondedInvitees();
    }
  }, [authLoading]);

  const handleAuthRedirects = () => {
    if (authLoading) return;

    if (isAuthenticated && user) {
      // Handle first login flow
      if (isFirstLogin() || mustChangePassword()) {
        router.replace({
          pathname: '/auth/change-password',
          params: { 
            employeeCode: user.employeeId,
            isFirstLogin: isFirstLogin().toString()
          },
        });
        return;
      }

      // Handle missing office type
      if (!user.officeType && !isAdmin()) {
        router.replace({
          pathname: '/auth/office-type',
          params: { employeeCode: user.employeeId },
        });
        return;
      }

      // Redirect admins to dashboard
      if (isAdmin()) {
        router.replace('/admin/dashboard');
        return;
      }
    }
  };

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
    router.push('/auth/login');
  };

  const handleEmployeeLogin = () => {
    router.push('/auth/login');
  };

  if (authLoading || loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#007bff" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show authenticated user view if logged in
  if (isAuthenticated && user && !isFirstLogin() && !mustChangePassword() && user.officeType) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Text style={styles.logoText}>PM Connect 3.0</Text>
              <Text style={styles.subtitle}>Welcome back, {user.employeeName}!</Text>
            </View>
            <TouchableOpacity style={styles.profileButton} onPress={() => router.push('/profile')}>
              <Text style={styles.profileButtonText}>👤</Text>
            </TouchableOpacity>
          </View>

          {/* User Dashboard Content */}
          <View style={styles.userDashboard}>
            <Text style={styles.dashboardTitle}>Your Dashboard</Text>
            
            <TouchableOpacity 
              style={styles.dashboardCard}
              onPress={() => router.push('/event-info')}
            >
              <Text style={styles.cardIcon}>📋</Text>
              <Text style={styles.cardTitle}>Event Information</Text>
              <Text style={styles.cardDescription}>View agenda, cab details, and event updates</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.dashboardCard}
              onPress={() => router.push('/gallery')}
            >
              <Text style={styles.cardIcon}>📸</Text>
              <Text style={styles.cardTitle}>Event Gallery</Text>
              <Text style={styles.cardDescription}>Browse photos and upload your memories</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.dashboardCard}
              onPress={() => router.push('/rsvp')}
            >
              <Text style={styles.cardIcon}>✉️</Text>
              <Text style={styles.cardTitle}>Update RSVP</Text>
              <Text style={styles.cardDescription}>Modify your event response if needed</Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Show public landing page for non-authenticated users
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoText}>PM Connect 3.0</Text>
            <Text style={styles.subtitle}>Event Management & Logistics</Text>
          </View>
        </View>

        {/* Login Options */}
        <View style={styles.loginSection}>
          <Text style={styles.loginTitle}>Sign in to continue</Text>
          
          <TouchableOpacity style={styles.loginOption} onPress={handleEmployeeLogin}>
            <Text style={styles.loginIcon}>👤</Text>
            <View style={styles.loginInfo}>
              <Text style={styles.loginOptionTitle}>Employee Login</Text>
              <Text style={styles.loginOptionDescription}>
                Sign in with your employee code and password
              </Text>
            </View>
            <Text style={styles.loginArrow}>→</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.loginOption} onPress={handleAdminLogin}>
            <Text style={styles.loginIcon}>🔐</Text>
            <View style={styles.loginInfo}>
              <Text style={styles.loginOptionTitle}>Admin Login</Text>
              <Text style={styles.loginOptionDescription}>
                Access admin dashboard and management tools
              </Text>
            </View>
            <Text style={styles.loginArrow}>→</Text>
          </TouchableOpacity>
        </View>

        {/* Legacy Access (for existing invitees without accounts) */}
        <View style={styles.legacySection}>
          <Text style={styles.legacySectionTitle}>Don't have login credentials?</Text>
          <Text style={styles.legacyDescription}>
            If you're an existing invitee, you can still access the old interface below:
          </Text>
          
          {unrespondedInvitees.length > 0 && (
            <View style={styles.inviteeList}>
              <Text style={styles.inviteeListTitle}>Quick RSVP Access:</Text>
              {unrespondedInvitees.slice(0, 3).map((invitee) => (
                <TouchableOpacity
                  key={invitee.employeeId}
                  style={styles.quickInviteeCard}
                  onPress={() => handleInviteeSelect(invitee)}
                >
                  <Text style={styles.quickInviteeName}>{invitee.employeeName}</Text>
                  <Text style={styles.quickInviteeId}>ID: {invitee.employeeId}</Text>
                </TouchableOpacity>
              ))}
              {unrespondedInvitees.length > 3 && (
                <Text style={styles.moreInvitees}>
                  +{unrespondedInvitees.length - 3} more invitees...
                </Text>
              )}
            </View>
          )}
        </View>

        {/* Information Section */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>New Authentication System</Text>
          <View style={styles.infoSteps}>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>1</Text>
              </View>
              <Text style={styles.stepText}>Use your Employee Code as username</Text>
            </View>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>2</Text>
              </View>
              <Text style={styles.stepText}>Initial password is your Employee Code</Text>
            </View>
            <View style={styles.infoStep}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>3</Text>
              </View>
              <Text style={styles.stepText}>Change password on first login</Text>
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
    marginTop: 12,
  },
  header: {
    backgroundColor: '#007bff',
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
  profileButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileButtonText: {
    fontSize: 20,
  },
  loginSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  loginTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 20,
    textAlign: 'center',
  },
  loginOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  loginIcon: {
    fontSize: 32,
    marginRight: 16,
  },
  loginInfo: {
    flex: 1,
  },
  loginOptionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 4,
  },
  loginOptionDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
  loginArrow: {
    fontSize: 20,
    color: '#007bff',
    fontWeight: 'bold',
    marginLeft: 12,
  },
  userDashboard: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  dashboardTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 20,
  },
  dashboardCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  cardIcon: {
    fontSize: 32,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
  legacySection: {
    padding: 24,
    backgroundColor: '#fff8e1',
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ffc107',
  },
  legacySectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 12,
  },
  legacyDescription: {
    fontSize: 14,
    color: '#856404',
    lineHeight: 20,
    marginBottom: 16,
  },
  inviteeList: {
    marginTop: 8,
  },
  inviteeListTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 12,
  },
  quickInviteeCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#f0c674',
  },
  quickInviteeName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#856404',
  },
  quickInviteeId: {
    fontSize: 12,
    color: '#856404',
    opacity: 0.8,
  },
  moreInvitees: {
    fontSize: 12,
    color: '#856404',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 8,
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