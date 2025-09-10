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
import * as DocumentPicker from 'expo-document-picker';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Invitee {
  employeeId: string;
  employeeName: string;
  cadre: string;
  projectName: string;
  hasResponded: boolean;
}

export default function AdminInvitees() {
  const [invitees, setInvitees] = useState<Invitee[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchInvitees();
  }, []);

  const fetchInvitees = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/invitees`);
      if (response.ok) {
        const data = await response.json();
        setInvitees(data);
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

  const handleBulkUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        setUploading(true);
        const asset = result.assets[0];
        
        const formData = new FormData();
        formData.append('file', {
          uri: asset.uri,
          name: asset.name,
          type: asset.mimeType || 'text/csv',
        } as any);

        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/invitees/bulk-upload`, {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.ok) {
          const data = await response.json();
          Alert.alert('Success', `Successfully uploaded ${data.inserted_count} invitees`);
          fetchInvitees(); // Refresh the list
        } else {
          const errorData = await response.json();
          Alert.alert('Upload Failed', errorData.detail || 'Failed to upload CSV');
        }
      }
    } catch (error) {
      console.error('Error uploading CSV:', error);
      Alert.alert('Error', 'Failed to select or upload file');
    } finally {
      setUploading(false);
    }
  };

  const renderInviteeCard = (invitee: Invitee) => (
    <View key={invitee.employeeId} style={styles.inviteeCard}>
      <View style={styles.inviteeInfo}>
        <View style={styles.inviteeHeader}>
          <Text style={styles.inviteeName}>{invitee.employeeName}</Text>
          <View style={[
            styles.statusBadge,
            invitee.hasResponded ? styles.respondedBadge : styles.pendingBadge
          ]}>
            <Text style={[
              styles.statusText,
              invitee.hasResponded ? styles.respondedText : styles.pendingText
            ]}>
              {invitee.hasResponded ? 'Responded' : 'Pending'}
            </Text>
          </View>
        </View>
        <Text style={styles.inviteeDetails}>ID: {invitee.employeeId}</Text>
        <Text style={styles.inviteeDetails}>{invitee.cadre}</Text>
        <Text style={styles.inviteeDetails}>{invitee.projectName}</Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Invitee Management</Text>
        </View>

        {/* Upload Section */}
        <View style={styles.uploadSection}>
          <Text style={styles.sectionTitle}>📤 Bulk Upload</Text>
          <Text style={styles.uploadDescription}>
            Upload a CSV or Excel file with columns: Employee ID, Employee Name, Cadre, Project Name
          </Text>
          <TouchableOpacity
            style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
            onPress={handleBulkUpload}
            disabled={uploading}
          >
            <Text style={styles.uploadButtonText}>
              {uploading ? '📄 Uploading...' : '📄 Select CSV/Excel File'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Invitees List */}
        <View style={styles.inviteesSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>👥 All Invitees ({invitees.length})</Text>
            <TouchableOpacity style={styles.refreshButton} onPress={fetchInvitees}>
              <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007bff" />
              <Text style={styles.loadingText}>Loading invitees...</Text>
            </View>
          ) : invitees.length === 0 ? (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No invitees found</Text>
              <Text style={styles.noDataSubtext}>Upload a CSV file to get started</Text>
            </View>
          ) : (
            <View style={styles.inviteesList}>
              {invitees.map(renderInviteeCard)}
            </View>
          )}
        </View>

        {/* Stats Summary */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>📊 Summary</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{invitees.length}</Text>
              <Text style={styles.statLabel}>Total Invitees</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>
                {invitees.filter(i => i.hasResponded).length}
              </Text>
              <Text style={styles.statLabel}>Responded</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>
                {invitees.filter(i => !i.hasResponded).length}
              </Text>
              <Text style={styles.statLabel}>Pending</Text>
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
  uploadSection: {
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
  uploadDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
    marginBottom: 16,
  },
  uploadButton: {
    backgroundColor: '#28a745',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  uploadButtonDisabled: {
    opacity: 0.6,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  inviteesSection: {
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
  inviteesList: {
    gap: 12,
  },
  inviteeCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  inviteeInfo: {
    flex: 1,
  },
  inviteeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  inviteeName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  respondedBadge: {
    backgroundColor: '#d4edda',
  },
  pendingBadge: {
    backgroundColor: '#fff3cd',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  respondedText: {
    color: '#155724',
  },
  pendingText: {
    color: '#856404',
  },
  inviteeDetails: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 2,
  },
  statsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
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
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
});