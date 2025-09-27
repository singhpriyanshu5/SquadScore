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
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useLocalSearchParams, useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';

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

interface PlayerScore {
  player_id: string;
  player_name: string;
  score: number;
}

interface TeamScore {
  team_id: string;
  team_name: string;
  score: number;
  player_ids: string[];
}

interface GroupStats {
  total_players: number;
  total_teams: number;
  total_games: number;
  most_played_game: string | null;
  top_player: any;
}

interface GameSession {
  id: string;
  group_id: string;
  game_name: string;
  game_date: string;
  player_scores: PlayerScore[];
  team_scores: TeamScore[];
  created_date: string;
}

type GameMode = 'individual' | 'team';

const DEFAULT_GAMES = [
  'Settlers of Catan',
  'Ticket to Ride',
  'Azul',
  'Splendor',
  'King of Tokyo',
  'Wingspan',
  'Scythe',
  'Terraforming Mars',
  'Pandemic',
  'Gloomhaven',
  'Dominion',
  'Monopoly',
  'Risk',
  'Dungeons & Dragons'
];

export default function GameScreen() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [gameMode, setGameMode] = useState<GameMode>('individual');
  const [gameName, setGameName] = useState('');
  const [customGameName, setCustomGameName] = useState('');
  const [gameDate, setGameDate] = useState(new Date());
  const [playerScores, setPlayerScores] = useState<Record<string, string>>({});
  const [teamScores, setTeamScores] = useState<Record<string, string>>({});
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  useFocusEffect(
    useCallback(() => {
      if (id) {
        loadData();
      }
    }, [id])
  );

  const loadData = async () => {
    try {
      await Promise.all([loadPlayers(), loadTeams()]);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadPlayers = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/players`);
    if (!response.ok) {
      throw new Error('Failed to load players');
    }
    const playersData = await response.json();
    setPlayers(playersData);
    
    // Initialize player scores
    const initialScores: Record<string, string> = {};
    playersData.forEach((player: Player) => {
      initialScores[player.id] = '';
    });
    setPlayerScores(initialScores);
  };

  const loadTeams = async () => {
    const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/groups/${id}/teams`);
    if (!response.ok) {
      throw new Error('Failed to load teams');
    }
    const teamsData = await response.json();
    setTeams(teamsData);
    
    // Initialize team scores
    const initialScores: Record<string, string> = {};
    teamsData.forEach((team: Team) => {
      initialScores[team.id] = '';
    });
    setTeamScores(initialScores);
  };

  const getPlayerName = (playerId: string) => {
    const player = players.find(p => p.id === playerId);
    return player ? player.player_name : 'Unknown Player';
  };

  const getTeamPlayers = (team: Team) => {
    return team.player_ids.map(id => getPlayerName(id)).join(', ');
  };

  const handleSubmitGame = async () => {
    // Validate inputs
    const finalGameName = gameName === 'Custom Game' ? customGameName.trim() : gameName;
    if (!finalGameName) {
      Alert.alert('Error', 'Please select or enter a game name');
      return;
    }

    const scoresData = gameMode === 'individual' ? playerScores : teamScores;
    const hasAnyScore = Object.values(scoresData).some(score => score.trim() !== '');
    
    if (!hasAnyScore) {
      Alert.alert('Error', 'Please enter at least one score');
      return;
    }

    // Validate numeric scores
    const invalidScores = Object.entries(scoresData).filter(([_, score]) => {
      if (score.trim() === '') return false;
      const numScore = parseInt(score.trim());
      return isNaN(numScore);
    });

    if (invalidScores.length > 0) {
      Alert.alert('Error', 'All scores must be valid numbers');
      return;
    }

    setSubmitting(true);
    try {
      const playerScoresData: PlayerScore[] = [];
      const teamScoresData: TeamScore[] = [];

      if (gameMode === 'individual') {
        Object.entries(playerScores).forEach(([playerId, score]) => {
          if (score.trim() !== '') {
            const player = players.find(p => p.id === playerId);
            if (player) {
              playerScoresData.push({
                player_id: playerId,
                player_name: player.player_name,
                score: parseInt(score.trim())
              });
            }
          }
        });
      } else {
        Object.entries(teamScores).forEach(([teamId, score]) => {
          if (score.trim() !== '') {
            const team = teams.find(t => t.id === teamId);
            if (team) {
              teamScoresData.push({
                team_id: teamId,
                team_name: team.team_name,
                score: parseInt(score.trim()),
                player_ids: team.player_ids
              });
            }
          }
        });
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/game-sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          group_id: id,
          game_name: finalGameName,
          game_date: gameDate.toISOString(),
          player_scores: playerScoresData,
          team_scores: teamScoresData
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to record game');
      }

      Alert.alert(
        'Game Recorded!',
        `${finalGameName} has been recorded successfully.`,
        [
          {
            text: 'Record Another',
            onPress: () => {
              // Reset form
              setGameName('');
              setCustomGameName('');
              setGameDate(new Date());
              setPlayerScores(prev => {
                const reset: Record<string, string> = {};
                Object.keys(prev).forEach(key => {
                  reset[key] = '';
                });
                return reset;
              });
              setTeamScores(prev => {
                const reset: Record<string, string> = {};
                Object.keys(prev).forEach(key => {
                  reset[key] = '';
                });
                return reset;
              });
            }
          },
          {
            text: 'View Dashboard',
            onPress: () => router.back()
          }
        ]
      );
    } catch (error) {
      console.error('Error recording game:', error);
      Alert.alert('Error', 'Failed to record game. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading game data...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (players.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyContainer}>
          <Ionicons name="people" size={80} color="#ccc" />
          <Text style={styles.emptyTitle}>No Players Found</Text>
          <Text style={styles.emptySubtitle}>
            Add players to your group before recording games.
          </Text>
          <TouchableOpacity
            style={styles.addPlayersButton}
            onPress={() => router.push(`/group/${id}/players`)}
          >
            <Text style={styles.addPlayersButtonText}>Add Players</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Game Name Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Game Name</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.gameChips}>
              {COMMON_GAMES.map((game) => (
                <TouchableOpacity
                  key={game}
                  style={[
                    styles.gameChip,
                    gameName === game && styles.gameChipSelected
                  ]}
                  onPress={() => setGameName(game)}
                  activeOpacity={0.7}
                >
                  <Text style={[
                    styles.gameChipText,
                    gameName === game && styles.gameChipTextSelected
                  ]}>
                    {game}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            
            {gameName === 'Custom Game' && (
              <TextInput
                style={styles.customGameInput}
                value={customGameName}
                onChangeText={setCustomGameName}
                placeholder="Enter custom game name"
                maxLength={50}
              />
            )}
          </View>

          {/* Game Mode Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Game Mode</Text>
            <View style={styles.modeSelector}>
              <TouchableOpacity
                style={[
                  styles.modeButton,
                  gameMode === 'individual' && styles.modeButtonSelected
                ]}
                onPress={() => setGameMode('individual')}
                activeOpacity={0.7}
              >
                <Ionicons 
                  name="person" 
                  size={20} 
                  color={gameMode === 'individual' ? 'white' : '#007AFF'} 
                />
                <Text style={[
                  styles.modeButtonText,
                  gameMode === 'individual' && styles.modeButtonTextSelected
                ]}>
                  Individual Players
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.modeButton,
                  gameMode === 'team' && styles.modeButtonSelected,
                  teams.length === 0 && styles.modeButtonDisabled
                ]}
                onPress={() => teams.length > 0 && setGameMode('team')}
                disabled={teams.length === 0}
                activeOpacity={0.7}
              >
                <Ionicons 
                  name="people" 
                  size={20} 
                  color={gameMode === 'team' ? 'white' : (teams.length > 0 ? '#007AFF' : '#ccc')} 
                />
                <Text style={[
                  styles.modeButtonText,
                  gameMode === 'team' && styles.modeButtonTextSelected,
                  teams.length === 0 && styles.modeButtonTextDisabled
                ]}>
                  Teams
                </Text>
              </TouchableOpacity>
            </View>
            
            {teams.length === 0 && (
              <Text style={styles.noTeamsHint}>
                Create teams first to enable team mode
              </Text>
            )}
          </View>

          {/* Date Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Game Date</Text>
            <Text style={styles.dateDisplay}>
              {format(gameDate, 'EEEE, MMMM d, yyyy')}
            </Text>
          </View>

          {/* Score Entry */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              {gameMode === 'individual' ? 'Player Scores' : 'Team Scores'}
            </Text>
            
            {gameMode === 'individual' ? (
              <View style={styles.scoresContainer}>
                {players.map((player) => (
                  <View key={player.id} style={styles.scoreRow}>
                    <View style={styles.playerInfo}>
                      <Text style={styles.playerName}>{player.player_name}</Text>
                    </View>
                    <TextInput
                      style={styles.scoreInput}
                      value={playerScores[player.id] || ''}
                      onChangeText={(text) => 
                        setPlayerScores(prev => ({ ...prev, [player.id]: text }))
                      }
                      placeholder="Score"
                      keyboardType="numeric"
                      returnKeyType="next"
                    />
                  </View>
                ))}
              </View>
            ) : (
              <View style={styles.scoresContainer}>
                {teams.map((team) => (
                  <View key={team.id} style={styles.scoreRow}>
                    <View style={styles.teamInfo}>
                      <Text style={styles.teamName}>{team.team_name}</Text>
                      <Text style={styles.teamPlayers}>{getTeamPlayers(team)}</Text>
                    </View>
                    <TextInput
                      style={styles.scoreInput}
                      value={teamScores[team.id] || ''}
                      onChangeText={(text) => 
                        setTeamScores(prev => ({ ...prev, [team.id]: text }))
                      }
                      placeholder="Score"
                      keyboardType="numeric"
                      returnKeyType="next"
                    />
                  </View>
                ))}
              </View>
            )}
            
            <View style={styles.scoreHint}>
              <Ionicons name="information-circle" size={16} color="#666" />
              <Text style={styles.hintText}>
                {gameMode === 'team' 
                  ? 'Team scores will be distributed equally among team members'
                  : 'Enter individual player scores'
                }
              </Text>
            </View>
          </View>

          {/* Submit button */}
          <TouchableOpacity
            style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
            onPress={handleSubmitGame}
            disabled={submitting}
            activeOpacity={0.8}
          >
            {submitting ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={24} color="white" />
                <Text style={styles.submitButtonText}>Record Game</Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
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
    marginBottom: 24,
  },
  addPlayersButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  addPlayersButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  gameChips: {
    marginBottom: 16,
  },
  gameChip: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
  },
  gameChipSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  gameChipText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  gameChipTextSelected: {
    color: 'white',
  },
  customGameInput: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
  },
  modeSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 8,
  },
  modeButtonSelected: {
    backgroundColor: '#007AFF',
  },
  modeButtonDisabled: {
    borderColor: '#e1e5e9',
  },
  modeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  modeButtonTextSelected: {
    color: 'white',
  },
  modeButtonTextDisabled: {
    color: '#ccc',
  },
  noTeamsHint: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  dateDisplay: {
    backgroundColor: 'white',
    borderWidth: 2,
    borderColor: '#e1e5e9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#1a1a1a',
  },
  scoresContainer: {
    gap: 12,
    marginBottom: 16,
  },
  scoreRow: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  teamInfo: {
    flex: 1,
  },
  teamName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  teamPlayers: {
    fontSize: 14,
    color: '#666',
  },
  scoreInput: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e1e5e9',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    textAlign: 'center',
    minWidth: 80,
    marginLeft: 16,
  },
  scoreHint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#e3f2fd',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  hintText: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    lineHeight: 18,
  },
  submitButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginTop: 16,
    marginBottom: 32,
    minHeight: 56,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginLeft: 8,
  },
});