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

interface Response {
  responseId: string;
  employeeId: string;
  mobileNumber: string;
  requiresAccommodation: boolean;
  arrivalDate?: string;
  departureDate?: string;
  foodPreference: string;
  submissionTimestamp: string;
}

export default function AdminResponses() {
  const [responses, setResponses] = useState<Response[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchResponses();
  }, []);

  const fetchResponses = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/responses`);
      if (response.ok) {
        const data = await response.json();
        setResponses(data);
      } else {
        Alert.alert('Error', 'Failed to fetch responses');
      }
    } catch (error) {
      console.error('Error fetching responses:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportResponses = async () => {
    setExporting(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/responses/export`);
      if (response.ok) {
        const data = await response.json();
        if (data.excel_data) {
          Alert.alert(
            'Export Successful',
            `Excel file "${data.filename}" has been generated successfully. In a production app, this would trigger a download.`,
            [{ text: 'OK' }]
          );
        } else {
          Alert.alert('No Data', data.message || 'No responses to export');
        }
      } else {
        Alert.alert('Export Failed', 'Failed to export responses');
      }
    } catch (error) {
      console.error('Error exporting responses:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const renderResponseCard = (response: Response) => (
    <View key={response.responseId} style={styles.responseCard}>
      <View style={styles.responseHeader}>
        <Text style={styles.employeeId}>Employee ID: {response.employeeId}</Text>
        <Text style={styles.submissionDate}>
          {new Date(response.submissionTimestamp).toLocaleDateString()}
        </Text>
      </View>
      
      <View style={styles.responseDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Mobile:</Text>
          <Text style={styles.detailValue}>{response.mobileNumber}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Accommodation:</Text>
          <View style={[
            styles.accommodationBadge,
            response.requiresAccommodation ? styles.accommodationYes : styles.accommodationNo
          ]}>
            <Text style={[
              styles.accommodationText,
              response.requiresAccommodation ? styles.accommodationYesText : styles.accommodationNoText
            ]}>
              {response.requiresAccommodation ? 'Required' : 'Not Required'}
            </Text>
          </View>
        </View>

        {response.requiresAccommodation && (
          <>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Arrival:</Text>
              <Text style={styles.detailValue}>{response.arrivalDate || 'N/A'}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Departure:</Text>
              <Text style={styles.detailValue}>{response.departureDate || 'N/A'}</Text>
            </View>
          </>
        )}

        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Food Preference:</Text>
          <View style={styles.foodBadge}>
            <Text style={styles.foodText}>{response.foodPreference}</Text>
          </View>
        </View>
      </View>
    </View>
  );

  const accommodationCount = responses.filter(r => r.requiresAccommodation).length;
  const foodPreferences = responses.reduce((acc, r) => {
    acc[r.foodPreference] = (acc[r.foodPreference] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Response Management</Text>
        </View>

        {/* Export Section */}
        <View style={styles.exportSection}>
          <Text style={styles.sectionTitle}>📤 Export Data</Text>
          <Text style={styles.exportDescription}>
            Export all RSVP responses to Excel format for further analysis
          </Text>
          <TouchableOpacity
            style={[styles.exportButton, exporting && styles.exportButtonDisabled]}
            onPress={handleExportResponses}
            disabled={exporting}
          >
            <Text style={styles.exportButtonText}>
              {exporting ? '📊 Exporting...' : '📊 Export to Excel'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Summary Stats */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>📊 Response Summary</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{responses.length}</Text>
              <Text style={styles.statLabel}>Total Responses</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{accommodationCount}</Text>
              <Text style={styles.statLabel}>Accommodation</Text>
            </View>
          </View>

          {Object.keys(foodPreferences).length > 0 && (
            <View style={styles.foodPreferencesCard}>
              <Text style={styles.foodPreferencesTitle}>🍽️ Food Preferences</Text>
              <View style={styles.foodPreferencesList}>
                {Object.entries(foodPreferences).map(([preference, count]) => (
                  <View key={preference} style={styles.foodPreferenceItem}>
                    <Text style={styles.foodPreferenceName}>{preference}</Text>
                    <Text style={styles.foodPreferenceCount}>{count}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>

        {/* Responses List */}
        <View style={styles.responsesSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>📋 All Responses ({responses.length})</Text>
            <TouchableOpacity style={styles.refreshButton} onPress={fetchResponses}>
              <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007bff" />
              <Text style={styles.loadingText}>Loading responses...</Text>
            </View>
          ) : responses.length === 0 ? (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No responses found</Text>
              <Text style={styles.noDataSubtext}>Responses will appear here once invitees submit their RSVP</Text>
            </View>
          ) : (
            <View style={styles.responsesList}>
              {responses.map(renderResponseCard)}
            </View>
          )}
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
  header: {
    backgroundColor: '#007bff',
    padding: 24,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    marginRight: 16,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  exportSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  exportDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
    marginBottom: 16,
  },
  exportButton: {
    backgroundColor: '#28a745',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  exportButtonDisabled: {
    opacity: 0.6,
  },
  exportButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6c757d',
    textAlign: 'center',
  },
  foodPreferencesCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  foodPreferencesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  foodPreferencesList: {
    gap: 8,
  },
  foodPreferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 8,
    backgroundColor: 'white',
    borderRadius: 6,
  },
  foodPreferenceName: {
    fontSize: 14,
    color: '#495057',
  },
  foodPreferenceCount: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#007bff',
  },
  responsesSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  refreshButton: {
    backgroundColor: '#007bff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#6c757d',
    marginTop: 16,
  },
  noDataContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noDataText: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 8,
  },
  noDataSubtext: {
    fontSize: 14,
    color: '#adb5bd',
    textAlign: 'center',
  },
  responsesList: {
    gap: 12,
  },
  responseCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  responseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  employeeId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  submissionDate: {
    fontSize: 12,
    color: '#6c757d',
  },
  responseDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  detailLabel: {
    fontSize: 14,
    color: '#6c757d',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 14,
    color: '#2c3e50',
  },
  accommodationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  accommodationYes: {
    backgroundColor: '#d4edda',
  },
  accommodationNo: {
    backgroundColor: '#f8d7da',
  },
  accommodationText: {
    fontSize: 12,
    fontWeight: '600',
  },
  accommodationYesText: {
    color: '#155724',
  },
  accommodationNoText: {
    color: '#721c24',
  },
  foodBadge: {
    backgroundColor: '#e2e3e5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  foodText: {
    fontSize: 12,
    color: '#495057',
    fontWeight: '500',
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