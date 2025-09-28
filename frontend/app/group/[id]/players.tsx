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
  TextInput,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Player {
  id: string;
  player_name: string;
  group_id: string;
  emoji: string;
  total_score: number;
  games_played: number;
  created_date: string;
}

const PLAYER_EMOJIS = [
  '😀', '😃', '😄', '😁', '😊', '😇', '🙂', '🙃', '😉', '😌',
  '😍', '🥰', '😘', '😗', '🤗', '🤔', '🤨', '😮', '😲', '🥳',
  '😎', '🤓', '🧐', '😏', '😒', '😞', '😔', '😟', '😕', '🙁',
  '😤', '😠', '😡', '🤬', '😱', '😨', '😰', '😥', '😢', '😭',
  '🤡', '🤠', '🥸', '🤫', '🤭', '🧙', '🧚', '🧛', '🧜', '🧞',
  '🤶', '🎅', '👸', '🤴', '👳', '👲', '🧕', '🤵', '👰', '🤰',
  '👶', '👧', '🧒', '👦', '👩', '🧑', '👨', '👵', '🧓', '👴',
  '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯',
  '🦁', '🐮', '🐷', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🦍'
];

export default function PlayersScreen() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [selectedEmoji, setSelectedEmoji] = useState('😀');
  const [addingPlayer, setAddingPlayer] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [updatingPlayer, setUpdatingPlayer] = useState(false);
  const [deletingPlayerId, setDeletingPlayerId] = useState<string | null>(null);
  const { id } = useLocalSearchParams<{ id: string }>();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadPlayers();
      }
    }, [id])
  );

  const loadPlayers = async () => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/players-normalized`);
      if (!response.ok) {
        throw new Error('Failed to load players');
      }
      const playersData = await response.json();
      setPlayers(playersData);
    } catch (error) {
      console.error('Error loading players:', error);
      Alert.alert('Error', 'Failed to load players. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadPlayers();
  };

  const handleAddPlayer = async () => {
    if (!newPlayerName.trim()) {
      Alert.alert('Error', 'Please enter a player name');
      return;
    }

    setAddingPlayer(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_name: newPlayerName.trim(),
          group_id: id,
          emoji: selectedEmoji,
        }),
      });

      if (response.status === 400) {
        Alert.alert('Error', 'A player with this name already exists in the group.');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to add player');
      }

      setNewPlayerName('');
      setSelectedEmoji('😀');
      setShowAddModal(false);
      loadPlayers();
    } catch (error) {
      console.error('Error adding player:', error);
      Alert.alert('Error', 'Failed to add player. Please try again.');
    } finally {
      setAddingPlayer(false);
    }
  };

  const handleEditPlayer = (player: Player) => {
    setEditingPlayer(player);
    setNewPlayerName(player.player_name);
    setSelectedEmoji(player.emoji);
    setShowEditModal(true);
  };

  const handleUpdatePlayer = async () => {
    if (!editingPlayer || !newPlayerName.trim()) {
      Alert.alert('Error', 'Please enter a player name');
      return;
    }

    setUpdatingPlayer(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players/${editingPlayer.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_name: newPlayerName.trim(),
          emoji: selectedEmoji,
        }),
      });

      if (response.status === 400) {
        Alert.alert('Error', 'A player with this name already exists in the group.');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to update player');
      }

      setNewPlayerName('');
      setSelectedEmoji('😀');
      setEditingPlayer(null);
      setShowEditModal(false);
      loadPlayers();
    } catch (error) {
      console.error('Error updating player:', error);
      Alert.alert('Error', 'Failed to update player. Please try again.');
    } finally {
      setUpdatingPlayer(false);
    }
  };

  const handleDeletePlayer = (player: Player) => {
    Alert.alert(
      'Delete Player',
      `Are you sure you want to delete "${player.player_name}"? This will remove them from all teams and game records.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => confirmDeletePlayer(player.id),
        },
      ]
    );
  };

  const confirmDeletePlayer = async (playerId: string) => {
    setDeletingPlayerId(playerId);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/players/${playerId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete player');
      }

      loadPlayers();
    } catch (error) {
      console.error('Error deleting player:', error);
      Alert.alert('Error', 'Failed to delete player. Please try again.');
    } finally {
      setDeletingPlayerId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getAverageScore = (player: Player) => {
    if (player.games_played === 0) return 0;
    return Math.round((player.total_score / player.games_played) * 100) / 100;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading players...</Text>
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
        {/* Add Player Button */}
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowAddModal(true)}
          activeOpacity={0.8}
        >
          <Ionicons name="person-add" size={24} color="white" />
          <Text style={styles.addButtonText}>Add New Player</Text>
        </TouchableOpacity>

        {/* Players List */}
        {players.length > 0 ? (
          <View style={styles.playersContainer}>
            <Text style={styles.sectionTitle}>Players ({players.length})</Text>
            {players.map((player) => (
              <View key={player.id} style={styles.playerCard}>
                <View style={styles.playerHeader}>
                  <TouchableOpacity
                    style={styles.playerInfo}
                    onPress={() => handleEditPlayer(player)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.playerNameRow}>
                      <Text style={styles.playerEmoji}>{player.emoji}</Text>
                      <Text style={styles.playerName}>{player.player_name}</Text>
                    </View>
                    <Text style={styles.joinedDate}>
                      Joined: {formatDate(player.created_date)}
                    </Text>
                  </TouchableOpacity>
                  
                  <View style={styles.playerActions}>
                    <TouchableOpacity
                      style={styles.deleteButton}
                      onPress={() => handleDeletePlayer(player)}
                      disabled={deletingPlayerId === player.id}
                      activeOpacity={0.7}
                    >
                      {deletingPlayerId === player.id ? (
                        <ActivityIndicator size="small" color="#ff4444" />
                      ) : (
                        <Ionicons name="trash" size={20} color="#ff4444" />
                      )}
                    </TouchableOpacity>
                  </View>
                </View>

                <View style={styles.playerStats}>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{player.total_score}</Text>
                    <Text style={styles.statSubValue}>({player.raw_total_score || 0})</Text>
                    <Text style={styles.statLabel}>Total Score</Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{player.games_played}</Text>
                    <Text style={styles.statLabel}>Games</Text>
                  </View>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{getAverageScore(player)}</Text>
                    <Text style={styles.statSubValue}>({player.raw_average_score || 0})</Text>
                    <Text style={styles.statLabel}>Average</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="people" size={80} color="#ccc" />
            <Text style={styles.emptyTitle}>No Players Yet</Text>
            <Text style={styles.emptySubtitle}>
              Add players to your group to start tracking scores!
            </Text>
          </View>
        )}
      </ScrollView>

      {/* Add Player Modal */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowAddModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.modalContent}
          >
            <View style={styles.modalHeader}>
              <TouchableOpacity
                onPress={() => setShowAddModal(false)}
                disabled={addingPlayer}
              >
                <Text style={styles.cancelButton}>Cancel</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>Add Player</Text>
              <TouchableOpacity
                onPress={handleAddPlayer}
                disabled={addingPlayer || !newPlayerName.trim()}
              >
                <Text style={[styles.saveButton, (!newPlayerName.trim() || addingPlayer) && styles.saveButtonDisabled]}>
                  {addingPlayer ? 'Adding...' : 'Add'}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Player Name</Text>
                <TextInput
                  style={styles.textInput}
                  value={newPlayerName}
                  onChangeText={setNewPlayerName}
                  placeholder="Enter player name"
                  maxLength={50}
                  autoFocus
                  returnKeyType="done"
                  onSubmitEditing={handleAddPlayer}
                />
              </View>

              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Choose Player Emoji</Text>
                <ScrollView 
                  horizontal 
                  showsHorizontalScrollIndicator={false}
                  style={styles.emojiScroll}
                  contentContainerStyle={styles.emojiScrollContent}
                >
                  {PLAYER_EMOJIS.map((emoji) => (
                    <TouchableOpacity
                      key={emoji}
                      style={[
                        styles.emojiButton,
                        selectedEmoji === emoji && styles.emojiButtonSelected
                      ]}
                      onPress={() => setSelectedEmoji(emoji)}
                      activeOpacity={0.7}
                    >
                      <Text style={styles.emojiText}>{emoji}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              <View style={styles.info}>
                <Ionicons name="information-circle" size={20} color="#666" />
                <Text style={styles.infoText}>
                  Player names must be unique within the group. Choose a fun emoji to represent this player!
                </Text>
              </View>
            </View>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>

      {/* Edit Player Modal */}
      <Modal
        visible={showEditModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowEditModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.modalContent}
          >
            <View style={styles.modalHeader}>
              <TouchableOpacity
                onPress={() => {
                  setShowEditModal(false);
                  setNewPlayerName('');
                  setSelectedEmoji('😀');
                  setEditingPlayer(null);
                }}
                disabled={updatingPlayer}
              >
                <Text style={styles.cancelButton}>Cancel</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>Edit Player</Text>
              <TouchableOpacity
                onPress={handleUpdatePlayer}
                disabled={updatingPlayer || !newPlayerName.trim()}
              >
                <Text style={[styles.saveButton, (!newPlayerName.trim() || updatingPlayer) && styles.saveButtonDisabled]}>
                  {updatingPlayer ? 'Updating...' : 'Update'}
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Player Name</Text>
                <TextInput
                  style={styles.textInput}
                  value={newPlayerName}
                  onChangeText={setNewPlayerName}
                  placeholder="Enter player name"
                  maxLength={50}
                  autoFocus
                  returnKeyType="done"
                />
              </View>

              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Choose Player Emoji</Text>
                <ScrollView 
                  horizontal 
                  showsHorizontalScrollIndicator={false}
                  style={styles.emojiScroll}
                  contentContainerStyle={styles.emojiScrollContent}
                >
                  {PLAYER_EMOJIS.map((emoji) => (
                    <TouchableOpacity
                      key={emoji}
                      style={[
                        styles.emojiButton,
                        selectedEmoji === emoji && styles.emojiButtonSelected
                      ]}
                      onPress={() => setSelectedEmoji(emoji)}
                      activeOpacity={0.7}
                    >
                      <Text style={styles.emojiText}>{emoji}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>

              <View style={styles.info}>
                <Ionicons name="information-circle" size={20} color="#666" />
                <Text style={styles.infoText}>
                  Update the player's name or emoji. Note: This won't change their game scores or statistics.
                </Text>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
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
  addButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 24,
    minHeight: 56,
  },
  addButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  playersContainer: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  playerCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 10,
  },
  playerStats: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 8,
  },
  statText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '500',
  },
  joinedDate: {
    fontSize: 12,
    color: '#999',
  },
  emojiScroll: {
    maxHeight: 200,
  },
  emojiScrollContent: {
    paddingHorizontal: 8,
  },
  emojiButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
    backgroundColor: '#f0f0f0',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  emojiButtonSelected: {
    backgroundColor: '#e3f2fd',
    borderColor: '#007AFF',
  },
  emojiText: {
    fontSize: 20,
  },
  playerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  playerInfo: {
    flex: 1,
  },
  playerNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  playerEmoji: {
    fontSize: 24,
    marginRight: 12,
  },
  playerName: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  joinedDate: {
    fontSize: 14,
    color: '#666',
  },
  playerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  deleteButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#ffe6e6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playerStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  statSubValue: {
    fontSize: 11,
    color: '#666',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
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
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  modalContent: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e5e9',
  },
  cancelButton: {
    fontSize: 16,
    color: '#666',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  saveButton: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  saveButtonDisabled: {
    color: '#ccc',
  },
  modalBody: {
    flex: 1,
    padding: 20,
  },
  inputContainer: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    minHeight: 48,
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