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
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface DashboardStats {
  totalInvitees: number;
  rsvpYes: number;
  rsvpNo: number;
  accommodationRequests: number;
  foodPreferences: {
    [key: string]: number;
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/dashboard/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        console.error('Failed to fetch stats:', response.status);
        Alert.alert('Error', 'Failed to fetch dashboard statistics');
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const navigateToSection = (section: string) => {
    router.push(`/admin/${section}`);
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Logout', 
          style: 'destructive',
          onPress: () => {
            try {
              router.replace('/');
            } catch (error) {
              console.error('Navigation error:', error);
              // Fallback navigation
              router.push('/');
            }
          }
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007bff" />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>Admin Dashboard</Text>
            <Text style={styles.headerSubtitle}>PM Connect 3.0</Text>
          </View>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>Logout</Text>
          </TouchableOpacity>
        </View>

        {/* Statistics Cards */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>📊 Event Statistics</Text>
          
          {stats && (
            <View style={styles.statsGrid}>
              <View style={[styles.statCard, styles.totalInviteesCard]}>
                <Text style={styles.statNumber}>{stats.totalInvitees}</Text>
                <Text style={styles.statLabel}>Total Invitees</Text>
              </View>
              
              <View style={[styles.statCard, styles.rsvpYesCard]}>
                <Text style={styles.statNumber}>{stats.rsvpYes}</Text>
                <Text style={styles.statLabel}>RSVP Yes</Text>
              </View>
              
              <View style={[styles.statCard, styles.rsvpNoCard]}>
                <Text style={styles.statNumber}>{stats.rsvpNo}</Text>
                <Text style={styles.statLabel}>Pending</Text>
              </View>
              
              <View style={[styles.statCard, styles.accommodationCard]}>
                <Text style={styles.statNumber}>{stats.accommodationRequests}</Text>
                <Text style={styles.statLabel}>Accommodation</Text>
              </View>
            </View>
          )}

          {/* Food Preferences */}
          {stats && Object.keys(stats.foodPreferences).length > 0 && (
            <View style={styles.foodPreferencesCard}>
              <Text style={styles.foodPreferencesTitle}>🍽️ Food Preferences</Text>
              <View style={styles.foodPreferencesList}>
                {Object.entries(stats.foodPreferences).map(([preference, count]) => (
                  <View key={preference} style={styles.foodPreferenceItem}>
                    <Text style={styles.foodPreferenceName}>{preference}</Text>
                    <Text style={styles.foodPreferenceCount}>{count}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>

        {/* Management Sections */}
        <View style={styles.managementSection}>
          <Text style={styles.sectionTitle}>🛠️ Management Tools</Text>
          
          <View style={styles.managementGrid}>
            <TouchableOpacity
              style={styles.managementCard}
              onPress={() => navigateToSection('invitees')}
            >
              <Text style={styles.managementIcon}>👥</Text>
              <Text style={styles.managementTitle}>Invitee Management</Text>
              <Text style={styles.managementDescription}>
                Upload CSV, view invitees, manage responses
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.managementCard}
              onPress={() => navigateToSection('responses')}
            >
              <Text style={styles.managementIcon}>📋</Text>
              <Text style={styles.managementTitle}>Response Management</Text>
              <Text style={styles.managementDescription}>
                View responses, export to Excel
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.managementCard}
              onPress={() => navigateToSection('agenda')}
            >
              <Text style={styles.managementIcon}>📄</Text>
              <Text style={styles.managementTitle}>Agenda Management</Text>
              <Text style={styles.managementDescription}>
                Upload and manage event agenda
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.managementCard}
              onPress={() => navigateToSection('gallery-admin')}
            >
              <Text style={styles.managementIcon}>📸</Text>
              <Text style={styles.managementTitle}>Gallery Management</Text>
              <Text style={styles.managementDescription}>
                View and manage event photos
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.managementCard}
              onPress={() => navigateToSection('cab-allocations')}
            >
              <Text style={styles.managementIcon}>🚗</Text>
              <Text style={styles.managementTitle}>Cab Allocations</Text>
              <Text style={styles.managementDescription}>
                Upload and manage cab assignments
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActionsSection}>
          <Text style={styles.sectionTitle}>⚡ Quick Actions</Text>
          
          <TouchableOpacity style={styles.quickActionButton} onPress={fetchDashboardStats}>
            <Text style={styles.quickActionText}>🔄 Refresh Statistics</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => navigateToSection('responses')}
          >
            <Text style={styles.quickActionText}>📤 Export All Responses</Text>
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
    backgroundColor: '#007bff',
    padding: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerContent: {
    flex: 1,
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
  logoutButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  logoutButtonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 14,
  },
  statsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    width: '48%',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  totalInviteesCard: {
    backgroundColor: '#e3f2fd',
  },
  rsvpYesCard: {
    backgroundColor: '#e8f5e8',
  },
  rsvpNoCard: {
    backgroundColor: '#fff3e0',
  },
  accommodationCard: {
    backgroundColor: '#f3e5f5',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
  },
  foodPreferencesCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  foodPreferencesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  foodPreferencesList: {
    gap: 12,
  },
  foodPreferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: 'white',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  foodPreferenceName: {
    fontSize: 16,
    color: '#495057',
  },
  foodPreferenceCount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007bff',
  },
  managementSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  managementGrid: {
    gap: 16,
  },
  managementCard: {
    padding: 20,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  managementIcon: {
    fontSize: 32,
    marginBottom: 12,
  },
  managementTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  managementDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
  quickActionsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  quickActionButton: {
    backgroundColor: '#007bff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  quickActionText: {
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
});