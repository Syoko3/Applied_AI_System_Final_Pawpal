from pawpal_system import (
    Task, Pet, Owner, Scheduler, Priority,
    generate_schedule_with_context,
    validate_schedule,
    review_and_fix_schedule,
    validate_and_fix_schedule
)
from rag_system import (
    RAGSystem,
    extract_text_from_pdf,
    chunk_text,
    chunk_text_by_sentences,
    generate_embeddings,
    search_similar_chunks,
    cosine_similarity,
)
from openai import OpenAI
from pathlib import Path
import uuid
import sys
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


MACHINE_LEARNING_KB = """
Machine Learning Fundamentals

Supervised Learning:
Supervised learning is a machine learning approach where models learn from labeled data.
Each training example includes both input features and the correct output (label).
Common supervised learning tasks include classification and regression.
Examples include predicting house prices, email spam detection, and image classification.

Unsupervised Learning:
Unsupervised learning works with unlabeled data to find patterns and structure.
The algorithm must discover meaningful patterns without guidance from labels.
Common techniques include clustering (k-means, hierarchical clustering) and dimensionality reduction.
Applications include customer segmentation, anomaly detection, and data visualization.

Deep Learning:
Deep learning uses artificial neural networks with multiple layers (hence "deep").
Convolutional Neural Networks (CNNs) excel at image processing and computer vision.
Recurrent Neural Networks (RNNs) are ideal for sequential data like text and time series.
Transformers have revolutionized natural language processing with attention mechanisms.

Reinforcement Learning:
Reinforcement learning trains agents through interaction with an environment.
The agent learns by receiving rewards for good actions and penalties for bad ones.
Applications include game playing, robotics, and autonomous driving.
Key concepts: states, actions, rewards, and Q-learning algorithms.

Model Evaluation:
Accuracy alone is insufficient for model evaluation. Use precision, recall, and F1-score.
Cross-validation helps assess model performance on unseen data.
ROC curves and confusion matrices visualize classification performance.
For regression, use metrics like Mean Squared Error (MSE) and R-squared.
"""

PLAYGROUND_PET_CARE_KB = """
Complete Pet Care Guide

Dog Care:
Dogs require regular exercise, proper nutrition, and consistent training.
Adult dogs need 1-2 hours of daily exercise depending on breed and energy level.
Feed high-quality dog food appropriate for age, size, and health status.
Regular veterinary checkups, vaccinations, and parasite prevention are essential.
Grooming frequency depends on coat type; brush regularly to prevent matting.
Socialization with other dogs and people promotes behavioral health.
Training should start early using positive reinforcement methods.

Cat Care:
Cats are independent but need attention and mental enrichment.
Provide a safe indoor environment with climbing spaces and hiding spots.
Feed 1-2 times daily with high-quality cat food rich in protein.
Cats need 15-20 minutes of playtime daily for exercise and stimulation.
Litter boxes should be cleaned daily, with one per cat plus one extra.
Regular grooming helps prevent matting and reduces shedding.
Annual veterinary checkups are important for detecting health issues early.

Small Pets (Hamsters, Guinea Pigs, Rabbits):
Small rodents need proper cage size with appropriate bedding and ventilation.
Provide a balanced diet specific to the species; supplements depend on diet type.
Handle gently and regularly to maintain socialization and prevent stress.
Clean cages weekly to maintain hygiene and prevent respiratory issues.
Provide enrichment activities and adequate space for natural behaviors.
Temperature control is critical; keep away from drafts and direct sunlight.

Fish Care:
Establish proper water conditions: pH, temperature, and filtration.
Feed appropriate amounts once or twice daily; avoid overfeeding.
Perform 25% water changes weekly to maintain water quality.
Regular tank maintenance includes cleaning filters and removing algae buildup.
Monitor fish for signs of disease or stress.
Different species have different requirements; research before purchasing.

Reptile Care:
Research specific species requirements before purchase; they have unique needs.
Provide appropriate heating, lighting, and humidity for the species.
Feed live or appropriately sized prey depending on the species.
Handle minimally to reduce stress; some species are more docile than others.
Regular veterinary checkups by exotic animal specialists are essential.
Create naturalistic environments with proper substrates and hiding places.
"""

NUTRITION_KB = """
Basic Nutrition Science

Macronutrients:
Carbohydrates provide energy and fiber for digestive health.
Proteins build and repair tissues; essential amino acids cannot be synthesized by the body.
Fats provide concentrated energy and support hormone production and brain function.
Balanced macronutrient ratios depend on individual goals and activity level.

Micronutrients:
Vitamins are essential for metabolism, immunity, and cellular function.
Vitamin D supports bone health and calcium absorption.
Vitamin C is crucial for immune function and collagen synthesis.
Minerals like calcium, iron, and zinc have specific biological roles.
Deficiencies can lead to serious health problems; supplementation may be needed.

Hydration:
Water is essential for all bodily functions; typically 8 glasses daily for adults.
Individual needs vary based on activity level, climate, and health status.
Dehydration impairs cognitive function and physical performance.
Monitor urine color as an indicator of hydration status.

Dietary Guidelines:
Balanced diet should include vegetables, fruits, whole grains, and lean proteins.
Limit processed foods, sugar, and excessive salt intake.
Portion control is important for maintaining healthy weight.
Consider individual health conditions when planning meals.
Consult nutrition professionals for specific dietary needs.
"""


def print_task_list(title, task_pairs):
    print(f"\n{title}")
    print("-" * len(title))
    for pet, task in task_pairs:
        status = "done" if task.is_completed else "pending"
        print(
            f"{task.time} | {pet.name:<4} | {task.title:<22} | "
            f"{task.priority.name:<8} | {status}"
        )


def run_test():
    owner = Owner(str(uuid.uuid4()), "Sohdai", "sohdai@gmail.com", "123-456-7890", "morning", 120)

    dog = Pet(str(uuid.uuid4()), "Dog", "Canine", "Labrador", 5)
    cat = Pet(str(uuid.uuid4()), "Cat", "Feline", "Siamese", 3)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # Add tasks out of order to demonstrate time sorting.
    task1 = Task("T1", "Feed the dog", "Care", 10, Priority.HIGH, "daily", "morning", "08:30")
    task2 = Task("T2", "Play with the cat", "Playing", 30, Priority.MEDIUM, "weekly", "morning", "08:30")
    task3 = Task("T3", "Take the dog for a walk", "Exercise", 60, Priority.HIGH, "weekly", "afternoon", "14:00")
    task4 = Task("T4", "Brush the cat", "Grooming", 15, Priority.LOW, "weekly", "evening", "21:00")
    task5 = Task("T5", "Give the dog medicine", "Medicine", 5, Priority.CRITICAL, "daily", "morning", "07:45")
    task4.mark_complete()

    dog.add_task(task1)
    dog.add_task(task3)
    dog.add_task(task5)
    cat.add_task(task2)
    cat.add_task(task4)

    scheduler = Scheduler(str(uuid.uuid4()), owner)

    all_tasks = owner.all_tasks()
    print_task_list("Tasks in added order", all_tasks)

    sorted_tasks = scheduler.sort_by_time([task for _, task in all_tasks])
    sorted_pairs = [(task.pet, task) for task in sorted_tasks]
    print_task_list("Tasks sorted by HH:MM time", sorted_pairs)

    print_task_list("Completed tasks only", scheduler.filter_tasks(is_completed=True))
    print_task_list("Cat tasks only", scheduler.filter_tasks(pet_name="Cat"))
    print_task_list(
        "Pending dog tasks only",
        scheduler.filter_tasks(is_completed=False, pet_name="Dog"),
    )

    conflict_warnings = scheduler.detect_time_conflicts()
    print("\nConflict warnings")
    print("-----------------")
    if conflict_warnings:
        for warning in conflict_warnings:
            print(warning)
    else:
        print("No time conflicts detected.")

    scheduler.generate_schedule()
    print("\nToday's Schedule:")
    if scheduler.generated_schedule and scheduler.generated_schedule.warnings:
        print("\nSchedule warnings")
        print("-----------------")
        for warning in scheduler.generated_schedule.warnings:
            print(warning)
    scheduler.display_plan()
    print(scheduler.explain_reasoning())


def run_validation_demo():
    """Demonstrate the schedule generation → validation → fix workflow."""
    print("\n" + "=" * 70)
    print("🐾 SCHEDULE GENERATION WITH VALIDATION & IMPROVEMENT")
    print("=" * 70)
    
    # Example 1: User input and context
    pet_info = {
        "type": "dog",
        "name": "Max",
        "breed": "Golden Retriever",
        "age": 3,
        "context": "Active dog, medium-energy, lives in suburban area"
    }
    
    user_request = f"Create a daily schedule for {pet_info['name']}, a {pet_info['age']}-year-old {pet_info['breed']}"
    pet_context = f"""
    Pet: {pet_info['name']}
    Type: {pet_info['type']}
    Breed: {pet_info['breed']}
    Age: {pet_info['age']} years
    Additional Info: {pet_info['context']}
    """
    
    print("\n📋 INPUT:")
    print(f"   Pet: {pet_info['name']} ({pet_info['breed']})")
    print(f"   Request: {user_request}")
    
    # Step 1: Generate schedule
    print("\n" + "-" * 70)
    print("STEP 1: Generate Schedule with LLM")
    print("-" * 70)
    print("🤖 Generating AI schedule...")
    
    try:
        generated_schedule = generate_schedule_with_context(user_request, pet_context)
        print("✅ Schedule generated")
        print(generated_schedule)
    except Exception as e:
        print(f"❌ Error generating schedule: {e}")
        return
    
    # Step 2: Validate schedule
    print("\n" + "-" * 70)
    print("STEP 2: Validate Generated Schedule")
    print("-" * 70)
    print("🔍 Validating schedule...")
    
    validation = validate_schedule(generated_schedule)
    
    print(f"\n📊 Validation Result: {validation['status'].upper()}")
    print(f"Summary: {validation['summary']}")
    print(f"Tasks detected: {validation['task_count']}")
    
    if validation['issues']:
        print("\n⚠️  Issues Found:")
        for i, issue in enumerate(validation['issues'], 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✅ No issues found - schedule is valid!")
    
    # Step 3: Fix if needed
    print("\n" + "-" * 70)
    print("STEP 3: Fix Schedule (if needed)")
    print("-" * 70)
    
    if validation['status'] == "invalid":
        print("🔧 Fixing schedule based on validation issues...")
        
        try:
            improved_schedule = review_and_fix_schedule(
                generated_schedule,
                validation['issues'],
                pet_info['type'],
                pet_info['context']
            )
            print("✅ Schedule improved")
            print(improved_schedule)
        except Exception as e:
            print(f"❌ Error improving schedule: {e}")
    else:
        print("✅ Schedule is already valid - no fixes needed!")
    
    # Step 4: Complete pipeline demonstration
    print("\n" + "-" * 70)
    print("STEP 4: Complete Pipeline (Generate → Validate → Fix)")
    print("-" * 70)
    print("🔄 Running complete validation and fixing pipeline...")
    
    try:
        full_result = validate_and_fix_schedule(
            generated_schedule,
            pet_info['type'],
            pet_info['context']
        )
        
        print(f"\n📊 Pipeline Result:")
        print(f"   Original valid: {full_result['is_valid']}")
        print(f"   Issues found: {len(full_result['validation_result']['issues'])}")
        
        if full_result['improved_schedule']:
            print(f"   ✅ Improved schedule generated")
            print(f"\n{full_result['improved_schedule']}")
        
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
    
    print("\n" + "=" * 70)
    print("✅ VALIDATION DEMO COMPLETE")
    print("=" * 70)


def run_rag_examples():
    """Run RAG system usage examples."""
    print("🔍 RAG System Examples")
    print("=" * 70)
    
    # Example 1: Basic RAG workflow with cosine similarity
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic RAG Usage (Cosine Similarity)")
    print("=" * 70)
    
    # Sample text for demonstration
    sample_text = """
    Artificial Intelligence (AI) is transforming healthcare by enabling faster diagnosis 
    and personalized treatment plans. Machine learning models can analyze medical images 
    and identify patterns invisible to human eyes.
    
    Deep learning networks have revolutionized natural language processing, allowing 
    computers to understand and generate human language with remarkable accuracy.
    
    Computer vision applications are now used in autonomous vehicles to detect objects, 
    read traffic signs, and navigate safely on roads.
    
    Reinforcement learning has enabled breakthrough achievements in game-playing AI, 
    surpassing human champions in complex strategic games.
    """
    
    # Create chunks manually for this example
    chunks = chunk_text_by_sentences(sample_text, target_chunk_size=300)
    print(f"\n📄 Created {len(chunks)} chunks from sample text")
    
    # Generate embeddings
    print("\n🔗 Generating embeddings...")
    embeddings = generate_embeddings(chunks)
    
    # Perform searches
    queries = [
        "medical diagnosis and AI",
        "autonomous vehicles",
        "games and learning",
    ]
    
    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        results = search_similar_chunks(query, chunks, embeddings, top_k=2)
        for i, (chunk, score) in enumerate(results, 1):
            print(f"   [{i}] Similarity: {score:.4f}")
            print(f"       {chunk[:100]}...")
    
    # Example 3: Comparing cosine similarity calculations
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Cosine Similarity Demonstration")
    print("=" * 70)
    
    # Simple embedding examples (low-dimensional for clarity)
    embedding_1 = [1.0, 0.0, 0.0]
    embedding_2 = [1.0, 0.0, 0.0]  # Same as 1
    embedding_3 = [0.0, 1.0, 0.0]  # Orthogonal to 1
    embedding_4 = [-1.0, 0.0, 0.0]  # Opposite to 1
    
    print("\nEmbeddings:")
    print(f"  e1: {embedding_1}")
    print(f"  e2: {embedding_2} (same as e1)")
    print(f"  e3: {embedding_3} (orthogonal to e1)")
    print(f"  e4: {embedding_4} (opposite to e1)")
    
    print("\nCosine Similarity Scores:")
    print(f"  e1 vs e2: {cosine_similarity(embedding_1, embedding_2):.4f} (identical)")
    print(f"  e1 vs e3: {cosine_similarity(embedding_1, embedding_3):.4f} (no relationship)")
    print(f"  e1 vs e4: {cosine_similarity(embedding_1, embedding_4):.4f} (opposite)")
    
    # Example 4: Comparing different chunking strategies
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Chunking Methods Comparison")
    print("=" * 70)
    
    sample_text_2 = """
    The development of artificial intelligence has been a gradual process. 
    Early AI research focused on symbolic reasoning and logic systems. 
    Later breakthroughs came through machine learning approaches. 
    Deep learning revolutionized the field in the 2010s. 
    Today, large language models demonstrate remarkable capabilities.
    """
    
    # Method 1: Character-based chunking
    char_chunks = chunk_text(sample_text_2, chunk_size=100, overlap=20)
    print(f"\n📄 Character-based chunking (size=100, overlap=20):")
    print(f"   Created {len(char_chunks)} chunks")
    for i, chunk in enumerate(char_chunks, 1):
        print(f"   [{i}] {chunk[:60]}...")
    
    # Method 2: Sentence-based chunking
    sentence_chunks = chunk_text_by_sentences(sample_text_2, target_chunk_size=150)
    print(f"\n📄 Sentence-based chunking (target=150):")
    print(f"   Created {len(sentence_chunks)} chunks")
    for i, chunk in enumerate(sentence_chunks, 1):
        print(f"   [{i}] {chunk[:60]}...")
    
    print("\n📝 Example 2 (PDF loading) requires a PDF file.")
    print("   Uncomment example_2_rag_system_class() to test with your own PDF.\n")


def demo_similarity_search(knowledge_base: str, title: str) -> None:
    """Run a demo of similarity search on a knowledge base."""
    print("\n" + "=" * 70)
    print(f"🔍 {title}")
    print("=" * 70)

    chunks = chunk_text_by_sentences(knowledge_base, target_chunk_size=300)
    print(f"\n📄 Created {len(chunks)} chunks")

    print("🔗 Generating embeddings... (this uses OpenAI API)")
    try:
        embeddings = generate_embeddings(chunks)
        print(f"✓ Generated embeddings for {len(embeddings)} chunks")
    except ValueError as e:
        print(f"⚠️  Error: {e}")
        return

    print("\n" + "-" * 70)
    demo_queries = [
        "What should I do first to learn machine learning?",
        "How do I care for a dog?",
        "What are the best foods to eat?",
    ]

    for query in demo_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            results = search_similar_chunks(query, chunks, embeddings, top_k=2)
            for i, (chunk, score) in enumerate(results, 1):
                print(f"   [{i}] Similarity: {score:.4f}")
                preview = chunk[:100].replace("\n", " ")
                print(f"       {preview}...")
        except Exception as e:
            print(f"   Error: {e}")


def demo_rag_system() -> None:
    """Demo RAG retrieval using combined in-memory knowledge bases."""
    print("\n" + "=" * 70)
    print("🔍 RAGSystem Class Demo")
    print("=" * 70)

    combined_kb = MACHINE_LEARNING_KB + "\n\n" + PLAYGROUND_PET_CARE_KB
    chunks = chunk_text_by_sentences(combined_kb, target_chunk_size=300)
    print(f"\n📄 Created {len(chunks)} chunks from combined knowledge base")

    print("🔗 Generating embeddings...")
    try:
        embeddings = generate_embeddings(chunks)
    except ValueError as e:
        print(f"Error: {e}")
        return

    test_queries = [
        "What is a CNN?",
        "How often should I exercise my dog?",
    ]

    print("\n" + "-" * 70)
    for query in test_queries:
        print(f"\n❓ Query: '{query}'")
        try:
            results = search_similar_chunks(query, chunks, embeddings, top_k=2)
            context_text = "\n\n".join([chunk for chunk, _ in results])
            print("\n📋 Retrieved Context:")
            print("-" * 70)
            print(context_text[:300] + "..." if len(context_text) > 300 else context_text)

            print("\n📊 Similarity Scores:")
            for i, (_chunk, score) in enumerate(results, 1):
                print(f"   Result {i}: {score:.4f}")
        except Exception as e:
            print(f"Error: {e}")


def benchmark_chunking() -> None:
    """Show the impact of different chunking strategies."""
    print("\n" + "=" * 70)
    print("📊 Chunking Strategy Comparison")
    print("=" * 70)

    sample_text = MACHINE_LEARNING_KB
    sizes = [200, 500, 1000]

    print(f"\nOriginal text length: {len(sample_text)} characters\n")

    for size in sizes:
        chunks = chunk_text(sample_text, chunk_size=size, overlap=50)
        avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
        print(f"Chunk size {size}:")
        print(f"  - Total chunks: {len(chunks)}")
        print(f"  - Average chunk size: {avg_chunk_size:.0f} characters")
        print(f"  - Coverage: {(sum(len(chunk) for chunk in chunks) / len(sample_text)) * 100:.1f}%\n")


def run_rag_playground() -> None:
    """Run the RAG playground demonstrations that used to live in rag_playground.py."""
    print("\n" + "🎮 RAG PLAYGROUND - Interactive Demonstrations\n")

    try:
        demo_similarity_search(
            MACHINE_LEARNING_KB,
            "Machine Learning Knowledge Base",
        )
        demo_similarity_search(
            PLAYGROUND_PET_CARE_KB,
            "Pet Care Knowledge Base",
        )
        demo_similarity_search(
            NUTRITION_KB,
            "Nutrition Knowledge Base",
        )
        demo_rag_system()
        benchmark_chunking()

        print("\n" + "=" * 70)
        print("✅ RAG Playground Complete!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("1. RAG retrieves relevant chunks from knowledge bases")
        print("2. Similarity scores indicate relevance (0-1 scale)")
        print("3. Chunking strategy affects retrieval quality")
        print("4. Works with any text-based knowledge base")
        print("\nNext Steps:")
        print("- Load your own PDFs with RAGSystem.load_pdf()")
        print("- Experiment with different chunk sizes")
        print("- Integrate with OpenAI for answer generation")
        print("=" * 70 + "\n")
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_pawpal_rag_example():
    """Run the PawPal RAG integration example."""
    print("\n" + "=" * 70)
    print("🐾 PawPal Pet Care Advisor (RAG-Powered)")
    print("=" * 70)
    
    # Create knowledge base
    print("\n📚 Loading pet care knowledge base...")
    chunks, embeddings, kb_text = create_pet_care_knowledge_base()
    print(f"   ✓ Created {len(chunks)} chunks from knowledge base")
    print(f"   ✓ Generated embeddings for all chunks")
    
    # Example queries
    example_queries = [
        "How much should I feed my Labrador?",
        "What exercise does my Lab need daily?",
        "My Lab's ears seem infected. What should I do?",
        "How do I manage my Lab's shedding?",
        "Is swimming good for Labradors?",
    ]
    
    print("\n" + "=" * 70)
    print("Running RAG-powered pet care queries...\n")
    
    for i, query in enumerate(example_queries, 1):
        print(f"[Query {i}] {query}")
        print("-" * 70)
        
        recommendation = get_pet_care_recommendation(query, chunks, embeddings)
        print(recommendation)
        print("\n" + "=" * 70 + "\n")


def create_pet_care_knowledge_base() -> tuple:
    """
    Create a sample pet care knowledge base (in memory).
    In production, this would be loaded from a PDF.
    """
    knowledge_base = """
    LABRADOR RETRIEVER CARE GUIDE
    
    Feeding Requirements:
    Labradors require 2-3 meals per day depending on age. Adult Labradors need about 
    25-30 calories per pound of body weight. A 70-pound Lab typically needs 1400-1750 calories daily.
    Feed high-quality dog food with appropriate protein (18-25%) and fat content.
    
    Exercise Needs:
    Large breed dogs like Labradors need 60-120 minutes of exercise daily. This can include 
    walks, running, swimming, and fetch. Lack of exercise can lead to behavioral issues.
    Swimming is excellent for Labradors due to their water-resistant coat and natural swimming ability.
    
    Health Monitoring:
    Regular vet checkups are essential every 6-12 months for adult dogs. Watch for signs of 
    hip dysplasia, which is common in Labradors. Maintain healthy weight to prevent joint problems.
    Keep vaccinations current and use preventative flea and tick treatments.
    
    Grooming:
    Labradors have double coats and shed moderately year-round, heavily during seasonal coat blows.
    Brush their coat 2-3 times per week to manage shedding. Bathe monthly or as needed.
    Trim nails every 4-6 weeks and clean ears weekly to prevent infections.
    
    Mental Stimulation:
    Labradors are intelligent and need mental enrichment beyond physical exercise.
    Use puzzle toys, training sessions, and interactive games. Lack of mental stimulation 
    can lead to destructive behavior.
    
    Training:
    Start training early with positive reinforcement. Labradors respond well to food motivation.
    They excel at obedience, retrieval training, and service dog work.
    Consistency and patience are key to successful training. 
    
    Temperature Management:
    Labradors have thick coats and tolerate cold weather well but struggle in hot climates.
    Never leave them in hot cars. Provide shade and fresh water during summer.
    Consider shorter walks during extreme heat to prevent heat exhaustion.
    
    Socialization:
    Properly socialized Labradors are friendly and outgoing. Expose puppies to various 
    environments, people, and other animals during the critical socialization period (8-16 weeks).
    Adult Labs should maintain regular social interactions with other dogs and people.
    
    Common Health Issues:
    - Hip and elbow dysplasia: genetic condition affecting large breeds
    - Obesity: can lead to joint problems; maintain healthy diet and exercise
    - Ear infections: floppy ears require regular cleaning
    - Bloat (gastric dilatation): emergency condition; feed multiple small meals
    - Hypothyroidism: affects metabolism; requires veterinary management
    """
    
    # Split into chunks
    chunks = chunk_text_by_sentences(knowledge_base, target_chunk_size=400)
    
    # Generate embeddings
    embeddings = generate_embeddings(chunks)
    
    return chunks, embeddings, knowledge_base


def get_pet_care_recommendation(query: str, chunks: list, embeddings: list) -> str:
    """
    Get a pet care recommendation based on the knowledge base using RAG.
    """
    # Find relevant chunks
    results = search_similar_chunks(query, chunks, embeddings, top_k=3)
    
    # Format context from retrieved chunks
    context = "\n".join([chunk for chunk, _ in results])
    
    # Use OpenAI to generate response based on context
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not set"
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""You are a helpful pet care advisor. Using the following knowledge base context, 
answer the user's question about pet care. Be specific and provide practical advice.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION:
{query}

Please provide a helpful, specific answer based on the context provided."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content


def run_schedule_generation_examples():
    """Run schedule generation examples."""
    # Example 1: Schedule for a dog
    user_input_1 = "Create a daily schedule for my 5-year-old Labrador. Include feeding, exercise, and playtime."
    
    context_1 = """
    Pet Care Guidelines:
    - Dogs need 2-3 meals per day
    - Large breeds require 60+ minutes of exercise daily
    - Playtime helps with mental stimulation
    - Feeding times should be consistent (morning, noon, evening)
    - Exercise should be done after meals to prevent bloating
    """
    
    print("\n--- EXAMPLE 1: DOG SCHEDULE ---")
    result_1 = generate_schedule_with_context(user_input_1, context_1)
    print(result_1)
    
    # Example 2: Schedule for a cat
    user_input_2 = "Create a daily routine schedule for my 3-year-old indoor cat."
    
    context_2 = """
    Pet Care Guidelines:
    - Cats are crepuscular (active at dawn and dusk)
    - Indoor cats need 12-16 hours of sleep per day
    - 2-3 meals per day is recommended
    - Playtime should be 15-30 minutes per session
    - Grooming and litter box maintenance
    - Enrichment activities prevent behavioral issues
    """
    
    print("\n--- EXAMPLE 2: CAT SCHEDULE ---")
    result_2 = generate_schedule_with_context(user_input_2, context_2)
    print(result_2)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validate":
            run_validation_demo()
        elif sys.argv[1] == "rag":
            run_rag_examples()
        elif sys.argv[1] == "pawpal_rag":
            run_pawpal_rag_example()
        elif sys.argv[1] == "playground":
            run_rag_playground()
        elif sys.argv[1] == "schedule":
            run_schedule_generation_examples()
        else:
            print("Usage: python main.py [validate|rag|pawpal_rag|playground|schedule]")
            print("  validate    - Run schedule validation demo")
            print("  rag         - Run RAG system examples")
            print("  pawpal_rag  - Run PawPal RAG integration example")
            print("  playground  - Run the merged RAG playground demos")
            print("  schedule    - Run schedule generation examples")
            print("  (no args)   - Run basic test")
    else:
        run_test()
