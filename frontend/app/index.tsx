import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  RefreshControl,
  Animated,
  PanResponder,
} from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Group {
  id: string;
  group_code: string;
  group_name: string;
  created_date: string;
}

// SwipeableGroupCard component
const SwipeableGroupCard = ({ 
  group, 
  onPress, 
  onRemove,
  onEdit
}: { 
  group: Group; 
  onPress: () => void; 
  onRemove: () => void;
  onEdit: () => void;
}) => {
  const translateX = new Animated.Value(0);

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => false,
    onMoveShouldSetPanResponder: (evt, gestureState) => {
      // Only respond to horizontal swipes that are significant enough
      const isHorizontalSwipe = Math.abs(gestureState.dx) > Math.abs(gestureState.dy);
      const isSignificantMovement = Math.abs(gestureState.dx) > 10;
      const isLeftSwipe = gestureState.dx < 0;
      
      return isHorizontalSwipe && isSignificantMovement && isLeftSwipe;
    },
    onPanResponderGrant: () => {
      // Reset any existing animation
      translateX.setOffset(translateX._value);
      translateX.setValue(0);
    },
    onPanResponderMove: (evt, gestureState) => {
      // Only allow left swipe and limit the distance
      if (gestureState.dx < 0 && gestureState.dx >= -160) {
        translateX.setValue(gestureState.dx);
      }
    },
    onPanResponderRelease: (evt, gestureState) => {
      translateX.flattenOffset();
      
      // If swiped far enough to the left, show action buttons
      if (gestureState.dx < -60) {
        Animated.spring(translateX, {
          toValue: -140,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }).start();
      } else {
        // Reset position if not swiped far enough
        Animated.spring(translateX, {
          toValue: 0,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }).start();
      }
    },
    onPanResponderTerminate: () => {
      // Reset position if gesture is interrupted
      translateX.flattenOffset();
      Animated.spring(translateX, {
        toValue: 0,
        useNativeDriver: true,
      }).start();
    },
  });

  const resetPosition = () => {
    Animated.spring(translateX, {
      toValue: 0,
      useNativeDriver: true,
    }).start();
  };

  return (
    <View style={styles.swipeableContainer}>
      <View style={styles.actionButtonsContainer}>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => {
            resetPosition();
            onEdit();
          }}
          activeOpacity={0.8}
        >
          <Ionicons name="pencil" size={18} color="white" />
          <Text style={styles.actionButtonText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.removeButton}
          onPress={() => {
            resetPosition();
            onRemove();
          }}
          activeOpacity={0.8}
        >
          <Ionicons name="trash" size={18} color="white" />
          <Text style={styles.actionButtonText}>Remove</Text>
        </TouchableOpacity>
      </View>
      
      <Animated.View
        style={[
          styles.groupCardContainer,
          { transform: [{ translateX }] }
        ]}
        {...panResponder.panHandlers}
      >
        <TouchableOpacity
          style={styles.groupCard}
          onPress={onPress}
          activeOpacity={0.7}
        >
          <View style={styles.groupInfo}>
            <Text style={styles.groupName}>{group.group_name}</Text>
            <Text style={styles.groupCode}>Code: {group.group_code}</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#666" />
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
};

export default function HomeScreen() {
  const [recentGroups, setRecentGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();

  // Load groups when screen comes into focus (e.g., after creating a new group)
  useFocusEffect(
    useCallback(() => {
      loadRecentGroups();
    }, [])
  );

  const loadRecentGroups = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) {
      setRefreshing(true);
    }
    
    try {
      const groups = await AsyncStorage.getItem('recent_groups');
      if (groups) {
        setRecentGroups(JSON.parse(groups));
      }
    } catch (error) {
      console.error('Error loading recent groups:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = useCallback(() => {
    loadRecentGroups(true);
  }, []);

  const removeGroupFromRecents = async (groupId: string) => {
    try {
      const updatedGroups = recentGroups.filter(group => group.id !== groupId);
      await AsyncStorage.setItem('recent_groups', JSON.stringify(updatedGroups));
      setRecentGroups(updatedGroups);
    } catch (error) {
      console.error('Error removing group from recents:', error);
      Alert.alert('Error', 'Failed to remove group from recents. Please try again.');
    }
  };

  const handleRemoveGroup = (group: Group) => {
    Alert.alert(
      'Remove Group',
      `Remove "${group.group_name}" from your recent groups? You can always rejoin using the group code: ${group.group_code}`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => removeGroupFromRecents(group.id)
        }
      ]
    );
  };

  const handleEditGroup = async (group: Group) => {
    Alert.prompt(
      'Edit Group Name',
      `Current name: ${group.group_name}\n\nEnter new group name:`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Save',
          onPress: async (newName) => {
            if (!newName || newName.trim() === '') {
              Alert.alert('Error', 'Group name cannot be empty');
              return;
            }

            if (newName.trim() === group.group_name) {
              return; // No change needed
            }

            try {
              const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${group.id}/name`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  group_name: newName.trim()
                }),
              });

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update group name');
              }

              // Update the group in recent groups list
              const updatedGroups = recentGroups.map(g => 
                g.id === group.id 
                  ? { ...g, group_name: newName.trim() }
                  : g
              );
              setRecentGroups(updatedGroups);
              await AsyncStorage.setItem('recent_groups', JSON.stringify(updatedGroups));

              Alert.alert('Success', 'Group name updated successfully!');
            } catch (error) {
              console.error('Error updating group name:', error);
              Alert.alert('Error', 'Failed to update group name. Please try again.');
            }
          }
        }
      ],
      'plain-text',
      group.group_name
    );
  };

  const handleGroupPress = (groupId: string) => {
    router.push(`/group/${groupId}`);
  };

  const handleCreateGroup = () => {
    router.push('/group/create');
  };

  const handleJoinGroup = () => {
    router.push('/group/join');
  };

  const clearRecentGroups = async () => {
    Alert.alert(
      'Clear Recent Groups',
      'Are you sure you want to clear all recent groups?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('recent_groups');
            setRecentGroups([]);
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollView} 
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>SquadScore</Text>
          <Text style={styles.subtitle}>Track game scores with your squad</Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={handleCreateGroup}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle" size={24} color="white" />
            <Text style={styles.primaryButtonText}>Create New Group</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={handleJoinGroup}
            activeOpacity={0.8}
          >
            <Ionicons name="people" size={24} color="#007AFF" />
            <Text style={styles.secondaryButtonText}>Join Existing Group</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Groups */}
        {recentGroups.length > 0 && (
          <View style={styles.recentContainer}>
            <View style={styles.recentHeader}>
              <Text style={styles.sectionTitle}>Recent Groups</Text>
              <View style={styles.headerActions}>
                <TouchableOpacity 
                  onPress={handleRefresh}
                  style={styles.refreshButton}
                  disabled={refreshing}
                >
                  <Ionicons 
                    name="refresh" 
                    size={20} 
                    color={refreshing ? "#999" : "#007AFF"} 
                  />
                </TouchableOpacity>
                <TouchableOpacity onPress={clearRecentGroups}>
                  <Text style={styles.clearText}>Clear</Text>
                </TouchableOpacity>
              </View>
            </View>

            {recentGroups.map((group) => (
              <SwipeableGroupCard
                key={group.id}
                group={group}
                onPress={() => handleGroupPress(group.id)}
                onRemove={() => handleRemoveGroup(group)}
              />
            ))}
          </View>
        )}

        {/* Empty State */}
        {recentGroups.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="game-controller" size={80} color="#ccc" />
            <Text style={styles.emptyTitle}>No Groups Yet</Text>
            <Text style={styles.emptySubtitle}>
              Create a new group or join an existing one to start tracking board game scores!
            </Text>
          </View>
        )}
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
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  actionsContainer: {
    gap: 16,
    marginBottom: 40,
  },
  actionButton: {
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
    borderColor: '#007AFF',
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
    color: '#007AFF',
    marginLeft: 8,
  },
  recentContainer: {
    marginBottom: 32,
  },
  recentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  refreshButton: {
    padding: 4,
  },
  clearText: {
    fontSize: 16,
    color: '#007AFF',
  },
  swipeableContainer: {
    marginBottom: 12,
    position: 'relative',
  },
  removeButtonContainer: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: 80,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  removeButton: {
    backgroundColor: '#ff4444',
    width: 80,
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
  },
  removeButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  groupCardContainer: {
    width: '100%',
    zIndex: 2,
  },
  groupCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  groupInfo: {
    flex: 1,
  },
  groupName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  groupCode: {
    fontSize: 14,
    color: '#666',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 32,
  },
});