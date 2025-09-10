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

interface CabAllocation {
  cabId: string;
  cabNumber: number;
  assignedMembers: string[];
  pickupLocation: string;
  pickupTime: string;
}

export default function AdminCabAllocations() {
  const [allocations, setAllocations] = useState<CabAllocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchCabAllocations();
  }, []);

  const fetchCabAllocations = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/cab-allocations`);
      if (response.ok) {
        const data = await response.json();
        setAllocations(data);
      } else {
        console.log('No cab allocations found');
      }
    } catch (error) {
      console.error('Error fetching cab allocations:', error);
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

        const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/cab-allocations/upload`, {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.ok) {
          const data = await response.json();
          Alert.alert('Success', `Successfully uploaded ${data.inserted_count} cab allocations`);
          fetchCabAllocations(); // Refresh the list
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

  const renderCabCard = (allocation: CabAllocation) => (
    <View key={allocation.cabId} style={styles.cabCard}>
      <View style={styles.cabHeader}>
        <Text style={styles.cabNumber}>🚗 Cab {allocation.cabNumber}</Text>
        <Text style={styles.memberCount}>
          {allocation.assignedMembers.length} member{allocation.assignedMembers.length !== 1 ? 's' : ''}
        </Text>
      </View>
      
      <View style={styles.cabDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>📍 Pickup Location:</Text>
          <Text style={styles.detailValue}>{allocation.pickupLocation}</Text>
        </View>
        
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>🕐 Pickup Time:</Text>
          <Text style={styles.detailValue}>{allocation.pickupTime}</Text>
        </View>
      </View>

      <View style={styles.membersSection}>
        <Text style={styles.membersTitle}>👥 Assigned Members:</Text>
        <View style={styles.membersList}>
          {allocation.assignedMembers.map((memberId, index) => (
            <View key={index} style={styles.memberItem}>
              <Text style={styles.memberText}>{memberId}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );

  const totalMembers = allocations.reduce((acc, cab) => acc + cab.assignedMembers.length, 0);
  const totalCabs = allocations.length;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Cab Allocations</Text>
        </View>

        {/* Upload Section */}
        <View style={styles.uploadSection}>
          <Text style={styles.sectionTitle}>📤 Upload Cab Allocations</Text>
          <Text style={styles.uploadDescription}>
            Upload a CSV or Excel file with columns: Cab Number, Employee ID, Pickup Location, Time
          </Text>
          <TouchableOpacity
            style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
            onPress={handleBulkUpload}
            disabled={uploading}
          >
            <Text style={styles.uploadButtonText}>
              {uploading ? '🚗 Uploading...' : '🚗 Select CSV/Excel File'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Summary Statistics */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>📊 Allocation Summary</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{totalCabs}</Text>
              <Text style={styles.statLabel}>Total Cabs</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{totalMembers}</Text>
              <Text style={styles.statLabel}>Total Members</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>
                {totalCabs > 0 ? Math.round(totalMembers / totalCabs * 10) / 10 : 0}
              </Text>
              <Text style={styles.statLabel}>Avg per Cab</Text>
            </View>
          </View>
        </View>

        {/* Cab Allocations List */}
        <View style={styles.allocationsSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🚗 All Cab Allocations ({totalCabs})</Text>
            <TouchableOpacity style={styles.refreshButton} onPress={fetchCabAllocations}>
              <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007bff" />
              <Text style={styles.loadingText}>Loading cab allocations...</Text>
            </View>
          ) : allocations.length === 0 ? (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>No cab allocations found</Text>
              <Text style={styles.noDataSubtext}>Upload a CSV file to get started</Text>
            </View>
          ) : (
            <View style={styles.allocationsList}>
              {allocations.map(renderCabCard)}
            </View>
          )}
        </View>

        {/* Instructions Section */}
        <View style={styles.instructionsSection}>
          <Text style={styles.sectionTitle}>💡 Instructions</Text>
          <View style={styles.instructionsList}>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>1</Text>
              <Text style={styles.instructionText}>
                Prepare CSV with columns: Cab Number, Employee ID, Pickup Location, Time
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>2</Text>
              <Text style={styles.instructionText}>
                Multiple employees can be assigned to the same cab number
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>3</Text>
              <Text style={styles.instructionText}>
                Upload the file and allocations will be grouped automatically
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>4</Text>
              <Text style={styles.instructionText}>
                Employees can view their cab details in the event information page
              </Text>
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
  statsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
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
  allocationsSection: {
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
  allocationsList: {
    gap: 16,
  },
  cabCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  cabHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  cabNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  memberCount: {
    fontSize: 12,
    color: '#6c757d',
    backgroundColor: '#e9ecef',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  cabDetails: {
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6c757d',
    fontWeight: '500',
    width: 140,
  },
  detailValue: {
    fontSize: 14,
    color: '#2c3e50',
    flex: 1,
  },
  membersSection: {
    borderTopWidth: 1,
    borderTopColor: '#dee2e6',
    paddingTop: 16,
  },
  membersTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  membersList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  memberItem: {
    backgroundColor: '#007bff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  memberText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  instructionsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  instructionsList: {
    gap: 16,
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  instructionNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007bff',
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  instructionText: {
    flex: 1,
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
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