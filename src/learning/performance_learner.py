"""
src/learning/performance_learner.py - Learn from performance data
"""

from src.database import get_performance_stats, get_topic_performance
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def learn_from_performance():
    """
    Analyze past performance and extract insights
    
    Returns:
        dict with insights for future content decisions
    """
    insights = {
        'top_topics': [],
        'best_hooks': [],
        'optimal_length': 30,
        'best_countries': [],
        'recommendations': []
    }
    
    try:
        # Get performance stats
        stats = get_performance_stats()
        logger.info(f"Performance stats: {stats}")
        
        # Get topic performance
        topic_perf = get_topic_performance()
        
        if topic_perf:
            insights['top_topics'] = topic_perf[:5]
        
        # Generate recommendations
        if stats.get('avg_views', 0) > 1000:
            insights['recommendations'].append("Views are good - continue current strategy")
        else:
            insights['recommendations'].append("Views low - try more viral topics")
        
        if stats.get('avg_retention', 0) > 70:
            insights['recommendations'].append("Retention good - keep video length")
        elif stats.get('avg_retention', 0) < 50:
            insights['recommendations'].append("Retention low - shorten videos or improve hooks")
        
        logger.info(f"Learning insights: {insights['recommendations']}")
        
    except Exception as e:
        logger.error(f"Learning failed: {e}")
        insights['recommendations'].append(f"Error: {e}")
    
    return insights


def update_scoring_weights(insights):
    """
    Update scoring weights based on performance
    (This would modify config in a real implementation)
    """
    # Placeholder for adaptive learning
    pass
