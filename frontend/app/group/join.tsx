import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Group {
  id: string;
  group_code: string;
  group_name: string;
  created_date: string;
}

export default function JoinGroupScreen() {
  const [groupCode, setGroupCode] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleJoinGroup = async () => {
    if (!groupCode.trim()) {
      Alert.alert('Error', 'Please enter a group code');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          group_code: groupCode.trim().toUpperCase(),
        }),
      });

      if (!response.ok) {
        if (response.status === 404) {
          Alert.alert('Group Not Found', 'The group code you entered does not exist. Please check the code and try again.');
        } else {
          throw new Error('Failed to join group');
        }
        return;
      }

      const group: Group = await response.json();

      // Save to recent groups
      await saveToRecentGroups(group);

      Alert.alert(
        'Joined Group!',
        `Welcome to "${group.group_name}"!`,
        [
          {
            text: 'OK',
            onPress: () => {
              router.replace(`/group/${group.id}`);
            },
          },
        ]
      );
    } catch (error) {
      console.error('Error joining group:', error);
      Alert.alert('Error', 'Failed to join group. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveToRecentGroups = async (group: Group) => {
    try {
      const existingGroups = await AsyncStorage.getItem('recent_groups');
      let groups: Group[] = existingGroups ? JSON.parse(existingGroups) : [];
      
      // Remove if already exists and add to front
      groups = groups.filter(g => g.id !== group.id);
      groups.unshift(group);
      
      // Keep only last 10 groups
      groups = groups.slice(0, 10);
      
      await AsyncStorage.setItem('recent_groups', JSON.stringify(groups));
    } catch (error) {
      console.error('Error saving to recent groups:', error);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  const formatGroupCode = (text: string) => {
    // Convert to uppercase and limit to 6 characters
    const formatted = text.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    setGroupCode(formatted);
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          <View style={styles.header}>
            <Ionicons name="enter" size={64} color="#007AFF" />
            <Text style={styles.title}>Join Group</Text>
            <Text style={styles.subtitle}>
              Enter the group code shared by your friend to join their board game group.
            </Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.label}>Group Code</Text>
            <TextInput
              style={styles.input}
              value={groupCode}
              onChangeText={formatGroupCode}
              placeholder="Enter 6-character code"
              maxLength={6}
              autoCapitalize="characters"
              autoFocus
              returnKeyType="done"
              onSubmitEditing={handleJoinGroup}
            />
            <Text style={styles.hint}>
              Group codes are 6 characters long (e.g., ABC123)
            </Text>
          </View>

          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={handleJoinGroup}
              disabled={loading || groupCode.length !== 6}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <>
                  <Ionicons name="log-in" size={20} color="white" />
                  <Text style={styles.primaryButtonText}>Join Group</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={handleCancel}
              disabled={loading}
              activeOpacity={0.8}
            >
              <Text style={styles.secondaryButtonText}>Cancel</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.info}>
            <Ionicons name="information-circle" size={20} color="#666" />
            <Text style={styles.infoText}>
              Ask your friend for the group code. They can find it in their group dashboard.
            </Text>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 16,
  },
  form: {
    marginBottom: 32,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  input: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 18,
    minHeight: 48,
    textAlign: 'center',
    letterSpacing: 2,
    fontWeight: '600',
  },
  hint: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  actions: {
    gap: 12,
    marginBottom: 32,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    minHeight: 56,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
  },
  primaryButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  secondaryButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
  },
  info: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#e3f2fd',
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});