import math
import statistics

def cohens_d(pre_scores, post_scores):
    """
    Compute Cohen's d effect size for paired data.
    """
    if len(pre_scores) == 0:
        return 0

    diffs = [post - pre for pre, post in zip(pre_scores, post_scores)]

    mean_diff = statistics.mean(diffs)
    std_diff = statistics.stdev(diffs) if len(diffs) > 1 else 1e-9

    return mean_diff / std_diff


def evaluate_simulation(students):
    pre_scores = [s.pre_score for s in students]
    post_scores = [s.post_score for s in students]

    # Learning Outcomes Metrics
  
    avg_pre = statistics.mean(pre_scores)
    avg_post = statistics.mean(post_scores)
    gain_score = avg_post - avg_pre
    effect = cohens_d(pre_scores, post_scores)

    # Misconception reduction ratio
    reduction_values = [
        (s.memory.initial_misconceptions - s.memory.misconceptions)
        / max(1, s.memory.initial_misconceptions)
        for s in students
    ]
    misconception_reduction = statistics.mean(reduction_values)


    # Engagement Metrics
    engagement_score = statistics.mean([s.engagement for s in students])
    participation_rate = sum(1 for s in students if s.participated) / len(students)

    # Question quality index (depth × count)
    question_quality = statistics.mean([
        (s.question_depth * max(1, s.questions_asked)) for s in students
    ])


    # Behavioral / Cognitive Metrics
   
    avg_time_on_task = statistics.mean([s.time_on_task for s in students])
    cognitive_load_index = statistics.mean([s.cognitive_load for s in students])

    
    # Retention Estimate
    # A simple decay model: retention = knowledge * exp(-load)
 
    retention_estimate = statistics.mean([
        s.knowledge_level * math.exp(-s.cognitive_load)
        for s in students
    ])

 
    # Final Metrics Dictionary
  
    return {
        "avg_pretest": round(avg_pre, 3),
        "avg_posttest": round(avg_post, 3),
        "gain_score": round(gain_score, 3),
        "effect_size": round(effect, 4),

        "misconception_reduction": round(misconception_reduction, 3),
        "engagement_score": round(engagement_score, 3),
        "participation_rate": round(participation_rate, 3),
        "question_quality_score": round(question_quality, 3),

        "avg_time_on_task": round(avg_time_on_task, 3),
        "cognitive_load_index": round(cognitive_load_index, 3),

        "retention_estimate": round(retention_estimate, 3)
    }
