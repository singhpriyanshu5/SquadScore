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
  total_score: number;
  games_played: number;
  created_date: string;
}

interface Team {
  id: string;
  team_name: string;
  group_id: string;
  player_ids: string[];
  total_score: number;
  games_played: number;
  created_date: string;
}

export default function TeamsScreen() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [selectedPlayerIds, setSelectedPlayerIds] = useState<string[]>([]);
  const [addingTeam, setAddingTeam] = useState(false);
  const { id } = useLocalSearchParams<{ id: string }>();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadData();
      }
    }, [id])
  );

  const loadData = async () => {
    try {
      await Promise.all([loadTeams(), loadPlayers()]);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadTeams = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/teams-normalized`);
    if (!response.ok) {
      throw new Error('Failed to load teams');
    }
    const teamsData = await response.json();
    setTeams(teamsData);
  };

  const loadPlayers = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/players`);
    if (!response.ok) {
      throw new Error('Failed to load players');
    }
    const playersData = await response.json();
    setPlayers(playersData);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleAddTeam = async () => {
    if (!newTeamName.trim()) {
      Alert.alert('Error', 'Please enter a team name');
      return;
    }

    if (selectedPlayerIds.length === 0) {
      Alert.alert('Error', 'Please select at least one player for the team');
      return;
    }

    setAddingTeam(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/teams`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team_name: newTeamName.trim(),
          group_id: id,
          player_ids: selectedPlayerIds,
        }),
      });

      if (response.status === 400) {
        Alert.alert('Error', 'A team with this name already exists in the group.');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to add team');
      }

      setNewTeamName('');
      setSelectedPlayerIds([]);
      setShowAddModal(false);
      loadData();
    } catch (error) {
      console.error('Error adding team:', error);
      Alert.alert('Error', 'Failed to add team. Please try again.');
    } finally {
      setAddingTeam(false);
    }
  };

  const togglePlayerSelection = (playerId: string) => {
    setSelectedPlayerIds(prev => 
      prev.includes(playerId) 
        ? prev.filter(id => id !== playerId)
        : [...prev, playerId]
    );
  };

  const getPlayerName = (playerId: string) => {
    const player = players.find(p => p.id === playerId);
    return player ? player.player_name : 'Unknown Player';
  };

  const getTeamPlayers = (team: Team) => {
    return team.player_ids.map(id => getPlayerName(id)).join(', ');
  };

  const getAverageScore = (team: Team) => {
    if (team.games_played === 0) return 0;
    return Math.round((team.total_score / team.games_played) * 100) / 100;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading teams...</Text>
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
        {/* Add Team Button */}
        <TouchableOpacity
          style={[styles.addButton, players.length === 0 && styles.addButtonDisabled]}
          onPress={() => setShowAddModal(true)}
          disabled={players.length === 0}
          activeOpacity={0.8}
        >
          <Ionicons name="people" size={24} color={players.length > 0 ? "white" : "#ccc"} />
          <Text style={[styles.addButtonText, players.length === 0 && styles.addButtonTextDisabled]}>
            Create New Team
          </Text>
        </TouchableOpacity>

        {players.length === 0 && (
          <View style={styles.noPlayersWarning}>
            <Ionicons name="warning" size={20} color="#ff9500" />
            <Text style={styles.warningText}>
              Add players first before creating teams
            </Text>
          </View>
        )}

        {/* Teams List */}
        {teams.length > 0 ? (
          <View style={styles.teamsContainer}>
            <Text style={styles.sectionTitle}>Teams ({teams.length})</Text>
            {teams.map((team) => (
              <View key={team.id} style={styles.teamCard}>
                <View style={styles.teamInfo}>
                  <Text style={styles.teamName}>{team.team_name}</Text>
                  <Text style={styles.teamPlayers}>
                    Players: {getTeamPlayers(team)}
                  </Text>
                  <View style={styles.teamStats}>
                    <Text style={styles.statText}>
                      Total Score: {team.total_score}
                    </Text>
                    <Text style={styles.statText}>
                      Games: {team.games_played}
                    </Text>
                    <Text style={styles.statText}>
                      Average: {getAverageScore(team)}
                    </Text>
                  </View>
                  <Text style={styles.createdDate}>
                    Created: {formatDate(team.created_date)}
                  </Text>
                </View>
                <View style={styles.teamActions}>
                  <View style={styles.teamIcon}>
                    <Ionicons name="people" size={24} color="#007AFF" />
                    <Text style={styles.teamMemberCount}>{team.player_ids.length}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        ) : players.length > 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="people" size={80} color="#ccc" />
            <Text style={styles.emptyTitle}>No Teams Yet</Text>
            <Text style={styles.emptySubtitle}>
              Create teams to play team-based board games!
            </Text>
          </View>
        ) : null}
      </ScrollView>

      {/* Add Team Modal */}
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
                onPress={() => {
                  setShowAddModal(false);
                  setNewTeamName('');
                  setSelectedPlayerIds([]);
                }}
                disabled={addingTeam}
              >
                <Text style={styles.cancelButton}>Cancel</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>Create Team</Text>
              <TouchableOpacity
                onPress={handleAddTeam}
                disabled={addingTeam || !newTeamName.trim() || selectedPlayerIds.length === 0}
              >
                <Text style={[styles.saveButton, (!newTeamName.trim() || selectedPlayerIds.length === 0 || addingTeam) && styles.saveButtonDisabled]}>
                  {addingTeam ? 'Creating...' : 'Create'}
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Team Name</Text>
                <TextInput
                  style={styles.textInput}
                  value={newTeamName}
                  onChangeText={setNewTeamName}
                  placeholder="Enter team name"
                  maxLength={50}
                  autoFocus
                  returnKeyType="done"
                />
              </View>

              <View style={styles.playersSelectionContainer}>
                <Text style={styles.inputLabel}>Select Players</Text>
                <Text style={styles.selectionHint}>
                  Choose players for this team ({selectedPlayerIds.length} selected)
                </Text>
                {players.map((player) => (
                  <TouchableOpacity
                    key={player.id}
                    style={[
                      styles.playerSelectItem,
                      selectedPlayerIds.includes(player.id) && styles.playerSelectItemSelected
                    ]}
                    onPress={() => togglePlayerSelection(player.id)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.playerSelectInfo}>
                      <Text style={[
                        styles.playerSelectName,
                        selectedPlayerIds.includes(player.id) && styles.playerSelectNameSelected
                      ]}>
                        {player.player_name}
                      </Text>
                      <Text style={styles.playerSelectStats}>
                        {player.total_score} points • {player.games_played} games
                      </Text>
                    </View>
                    <View style={[
                      styles.checkbox,
                      selectedPlayerIds.includes(player.id) && styles.checkboxSelected
                    ]}>
                      {selectedPlayerIds.includes(player.id) && (
                        <Ionicons name="checkmark" size={16} color="white" />
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={styles.info}>
                <Ionicons name="information-circle" size={20} color="#666" />
                <Text style={styles.infoText}>
                  Team scores will be automatically distributed equally among team members.
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
  addButtonDisabled: {
    backgroundColor: '#e1e5e9',
  },
  addButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
  addButtonTextDisabled: {
    color: '#ccc',
  },
  noPlayersWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff3cd',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    gap: 12,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#856404',
  },
  teamsContainer: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  teamCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  teamInfo: {
    flex: 1,
  },
  teamName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  teamPlayers: {
    fontSize: 14,
    color: '#007AFF',
    marginBottom: 8,
  },
  teamStats: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 8,
  },
  statText: {
    fontSize: 14,
    color: '#666',
  },
  createdDate: {
    fontSize: 12,
    color: '#999',
  },
  teamActions: {
    marginLeft: 16,
    alignItems: 'center',
  },
  teamIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e3f2fd',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  teamMemberCount: {
    position: 'absolute',
    bottom: -8,
    fontSize: 12,
    fontWeight: 'bold',
    color: '#007AFF',
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
  playersSelectionContainer: {
    marginBottom: 24,
  },
  selectionHint: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  playerSelectItem: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#e1e5e9',
  },
  playerSelectItemSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#f0f8ff',
  },
  playerSelectInfo: {
    flex: 1,
  },
  playerSelectName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  playerSelectNameSelected: {
    color: '#007AFF',
  },
  playerSelectStats: {
    fontSize: 14,
    color: '#666',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#e1e5e9',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 16,
  },
  checkboxSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
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