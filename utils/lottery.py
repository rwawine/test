"""
Lottery system with cryptographically secure random number generation
"""

import hashlib
import secrets
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from database import DatabaseManager

logger = logging.getLogger(__name__)

class LotterySystem:
    """Cryptographically fair lottery system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def generate_seed(self) -> Tuple[str, str]:
        """
        Generate cryptographically secure random seed and its hash
        Returns: (seed, seed_hash)
        """
        # Generate random seed (32 bytes = 256 bits)
        seed = secrets.token_hex(32)
        
        # Create hash for public verification
        seed_hash = hashlib.sha256(seed.encode()).hexdigest()
        
        logger.info(f"Generated lottery seed hash: {seed_hash}")
        return seed, seed_hash
    
    def deterministic_random(self, seed: str, max_value: int, index: int = 0) -> int:
        """
        Generate deterministic random number from seed
        
        Args:
            seed: Random seed string
            max_value: Maximum value (exclusive)
            index: Index for generating multiple numbers from same seed
            
        Returns:
            Random number between 0 and max_value-1
        """
        # Combine seed with index for multiple draws
        combined = f"{seed}:{index}"
        
        # Create SHA-256 hash
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        
        # Convert first 8 bytes to integer
        random_int = int.from_bytes(hash_bytes[:8], byteorder='big')
        
        # Return value in range [0, max_value)
        return random_int % max_value
    
    def get_eligible_participants(self) -> List[Dict]:
        """Get all approved participants eligible for lottery"""
        participants = self.db_manager.get_all_participants(status='approved')
        
        # Filter out previous winners (if implementing single-win rule)
        eligible = []
        winners = self.db_manager.get_winners()
        winner_ids = {winner['participant_id'] for winner in winners}
        
        for participant in participants:
            if participant['id'] not in winner_ids:
                eligible.append(participant)
        
        logger.info(f"Found {len(eligible)} eligible participants")
        return eligible
    
    def conduct_lottery(self, num_winners: int = 1, exclude_previous: bool = True) -> Dict:
        """
        Conduct fair lottery draw
        
        Args:
            num_winners: Number of winners to select
            exclude_previous: Whether to exclude previous winners
            
        Returns:
            Dictionary with lottery results
        """
        participants = self.get_eligible_participants()
        
        if len(participants) == 0:
            raise ValueError("No eligible participants found")
        
        if num_winners > len(participants):
            raise ValueError(f"Cannot select {num_winners} winners from {len(participants)} participants")
        
        # Generate seed and hash
        seed, seed_hash = self.generate_seed()
        
        # Select winners using deterministic algorithm
        winners = []
        remaining_participants = participants.copy()
        
        for i in range(num_winners):
            if not remaining_participants:
                break
            
            # Generate random index
            random_index = self.deterministic_random(seed, len(remaining_participants), i)
            
            # Select winner
            winner = remaining_participants.pop(random_index)
            winners.append(winner)
            
            logger.info(f"Selected winner {i+1}: {winner['full_name']} (index: {random_index})")
        
        # Save results to database
        draw_number = len(self.db_manager.get_winners()) + 1
        
        winner_records = []
        for winner in winners:
            winner_id = self.db_manager.add_winner(
                participant_id=winner['id'],
                seed_hash=seed_hash,
                draw_number=draw_number
            )
            winner_records.append({
                'winner_id': winner_id,
                'participant': winner
            })
        
        # Prepare result
        result = {
            'success': True,
            'draw_date': datetime.now().isoformat(),
            'seed_hash': seed_hash,
            'seed': seed,  # Keep private! Only for verification
            'draw_number': draw_number,
            'total_participants': len(participants),
            'winners': winner_records,
            'algorithm': 'SHA-256 deterministic selection'
        }
        
        logger.info(f"Lottery completed: {len(winners)} winners selected from {len(participants)} participants")
        return result
    
    def verify_lottery_result(self, seed: str, seed_hash: str, 
                            participants: List[Dict], winners: List[Dict]) -> bool:
        """
        Verify that lottery result is correct given the seed
        
        Args:
            seed: Original seed used in lottery
            seed_hash: Hash of the seed
            participants: List of participants at time of draw
            winners: Selected winners
            
        Returns:
            True if result is verified, False otherwise
        """
        try:
            # Verify seed hash
            calculated_hash = hashlib.sha256(seed.encode()).hexdigest()
            if calculated_hash != seed_hash:
                logger.error("Seed hash verification failed")
                return False
            
            # Recreate the selection process
            remaining_participants = participants.copy()
            verified_winners = []
            
            for i in range(len(winners)):
                if not remaining_participants:
                    break
                
                random_index = self.deterministic_random(seed, len(remaining_participants), i)
                winner = remaining_participants.pop(random_index)
                verified_winners.append(winner)
            
            # Compare results
            winner_ids = {w['id'] for w in winners}
            verified_ids = {w['id'] for w in verified_winners}
            
            is_valid = winner_ids == verified_ids
            
            if is_valid:
                logger.info("Lottery result verification: PASSED")
            else:
                logger.error("Lottery result verification: FAILED")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False
    
    def get_lottery_statistics(self) -> Dict:
        """Get lottery statistics"""
        winners = self.db_manager.get_winners()
        participants = self.db_manager.get_all_participants()
        
        stats = {
            'total_draws': len(set(w['draw_number'] for w in winners)),
            'total_winners': len(winners),
            'total_participants': len(participants),
            'eligible_participants': len(self.get_eligible_participants()),
            'win_rate': len(winners) / len(participants) * 100 if participants else 0,
            'last_draw_date': max([w['draw_date'] for w in winners]) if winners else None
        }
        
        return stats
    
    def create_public_proof(self, result: Dict) -> Dict:
        """
        Create public proof of lottery fairness
        (without revealing the seed)
        """
        proof = {
            'draw_date': result['draw_date'],
            'seed_hash': result['seed_hash'],
            'draw_number': result['draw_number'],
            'total_participants': result['total_participants'],
            'num_winners': len(result['winners']),
            'algorithm': result['algorithm'],
            'verification_instructions': {
                'step1': 'Verify that SHA-256(seed) equals the published seed_hash',
                'step2': 'Use the deterministic algorithm with the seed to reproduce results',
                'step3': 'Compare your calculated winners with published results'
            }
        }
        
        return proof