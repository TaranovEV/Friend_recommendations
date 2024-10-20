from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def create_dataframe_for_N_recommendation(*, base_file_path: str) -> DataFrame:
    """
    Creates a DataFrame for N friend recommendations from a given file.

    This function reads a text file where each line contains a user ID followed by a list of their friends' IDs.
    It processes the file to create a DataFrame with two columns: 'user' and 'friends', where 'friends' is a list of
    integers representing the IDs of the user's friends.

    Parameters:
        base_file_path (str): The file path to the input text file containing user-friend pairs.

    Returns:
        DataFrame: A Spark DataFrame with two columns: 'user' (int) and 'friends' (list of int).

    Raises:
        ValueError: If the input file is not in the expected format.
    """
    spark = SparkSession.builder.appName("FriendRecommendations").getOrCreate()

    lines = spark.sparkContext.textFile(base_file_path)
    friend_pairs = lines.map(lambda line: line.split(" ", 1)).map(
        lambda pair: (int(pair[0]), list(map(int, pair[1].split(","))))
    )

    data = friend_pairs.collect()
    df = spark.createDataFrame(data, ["user", "friends"])
    return df


def create_dataframe_for_probability(*, secondary_file_path: str) -> DataFrame:
    """
    Creates a DataFrame for probability calculations from a given secondary data file.

    This function reads a text file where each line contains an ID followed by demographic information
    of individuals, including gender, age, city, and education status. It processes the file to create
    a DataFrame with the following columns: 'ID', 'Пол' (gender), 'Возраст' (age), 'Город' (city),
    and 'Высшее образование' (higher education).

    Parameters:
        secondary_file_path (str): The file path to the input text file containing demographic data.

    Returns:
        DataFrame: A Spark DataFrame with columns: 'ID' (int), 'Пол' (int), 'Возраст' (int),
                    'Город' (int), and 'Высшее образование' (int).

    Raises:
        ValueError: If the input file is not in the expected format or if there are any conversion issues.
    """
    spark = SparkSession.builder.appName("FriendRecommendations").getOrCreate()

    lines = spark.sparkContext.textFile(secondary_file_path)
    data = lines.map(lambda line: line.split(" ", 1)).map(
        lambda parts: (int(parts[0].strip()), *parts[1].split(", "))
    )

    data = data.map(
        lambda parts: (
            int(parts[0]),
            int(parts[1]),
            int(parts[2]),
            int(parts[3]),
            int(parts[4].strip()),
        )
    )

    df = spark.createDataFrame(
        data, ["ID", "Пол", "Возраст", "Город", "Высшее образование"]
    )
    return df


def get_N_recommendation(*, base_file_path: str, N: int) -> DataFrame:
    """
    Generates the top N friend recommendations for users based on their friends' friends.

    This function creates a DataFrame of user-friend relationships from a specified
    base file path, then identifies potential friends for each user by examining
    their friends' friends. It filters out existing friends and self-recommendations,
    ultimately returning the top N recommendations based on the number of common friends.

    Args:
        base_file_path (str): The path to the base file containing user-friend relationships.
                               The file should contain user IDs and their corresponding friends' IDs.
        N (int): The number of top friend recommendations to return for each user.

    Returns:
        DataFrame: A DataFrame containing the user, their potential friend (friend of a friend),
                    and the rank of the recommendation based on the number of common friends.
                    The DataFrame will have the following columns:
                    - user: The ID of the user for whom recommendations are being generated.
                    - fof: The ID of the recommended friend (friend of a friend).
                    - rank: The rank of the recommendation based on the number of common friends.
    """
    df = create_dataframe_for_N_recommendation(base_file_path=base_file_path)

    df = df.withColumn("friends", F.col("friends").cast("array<bigint>"))

    friends_exploded = df.withColumn("friend", F.explode(F.col("friends")))

    friends_of_friends = (
        friends_exploded.alias("df1")
        .join(friends_exploded.alias("df2"), F.col("df1.friend") == F.col("df2.user"))
        .select(
            F.col("df1.user").alias("user"),
            F.col("df1.friends").alias("friends"),
            F.col("df1.friend").alias("friend"),
            F.col("df2.friend").alias("fof"),
        )
    )

    recommendations = friends_of_friends.filter(F.col("user") != F.col("fof"))
    recommendations = recommendations.filter(
        ~F.array_contains(F.col("friends"), F.col("fof"))
    )

    friend_recommendations = recommendations.groupBy("user", "fof").agg(
        F.sum("friend").alias("common_friends")
    )

    window = Window.partitionBy("user").orderBy(F.col("common_friends").desc())
    top_n_recommendations = friend_recommendations.withColumn(
        "rank", F.row_number().over(window)
    ).filter(F.col("rank") <= N)
    top_n_recommendations = top_n_recommendations.select("user", "fof", "rank")

    return top_n_recommendations


def get_probability(*, top_n_recommendations, secondary_file_path: str) -> DataFrame:
    """
    Calculates the probability that two users will become friends based on various demographic factors.

    The target variable represents the probability that two users will become friends.
    We can create this probability based on different factors by assigning a weight to each factor.
    For example:

    Gender:
        - If genders match: +0.3
        - If genders differ: +0.1

    Age:
        - If the age difference is less than 5 years: +0.4
        - If the age difference is between 5 and 10 years: +0.2
        - If the age difference is greater than 10 years: -0.2

    City:
        - If they are in the same city: +0.5

    Higher Education:
        - Both have higher education: +0.3
        - One has higher education: +0.1

    Args:
        top_n_recommendations: A DataFrame containing the top N friend recommendations.
        secondary_file_path (str): The file path to the secondary data containing user demographic information.

    Returns:
        DataFrame: A DataFrame with calculated probabilities for each pair of users, along with their demographic information.
    """

    additional_properties = create_dataframe_for_probability(
        secondary_file_path=secondary_file_path
    )

    recommendations = (
        top_n_recommendations.join(
            additional_properties,
            top_n_recommendations.user == additional_properties.ID,
            "left",
        )
        .drop(additional_properties.ID)
        .withColumnRenamed("Пол", "user_gender")
        .withColumnRenamed("Возраст", "user_age")
        .withColumnRenamed("Город", "user_city")
        .withColumnRenamed("Высшее образование", "user_education")
    )

    recommendations = (
        recommendations.join(
            additional_properties,
            recommendations.fof == additional_properties.ID,
            "left",
        )
        .drop(additional_properties.ID)
        .withColumnRenamed("Пол", "potential_friend_gender")
        .withColumnRenamed("Возраст", "potential_friend_age")
        .withColumnRenamed("Город", "potential_friend_city")
        .withColumnRenamed("Высшее образование", "potential_friend_education")
    )

    recommendations = recommendations.withColumn(
        "probability",
        F.when(F.col("user_age") == F.col("potential_friend_gender"), 0.3).otherwise(
            0.1
        ),
    )

    recommendations = recommendations.withColumn(
        "probability",
        F.when(
            F.abs(F.col("user_age") - F.col("potential_friend_age")) < 5,
            F.col("probability") + 0.4,
        )
        .when(
            F.abs(F.col("user_age") - F.col("potential_friend_age")) < 10,
            F.col("probability") + 0.2,
        )
        .when(
            F.abs(F.col("user_age") - F.col("potential_friend_age")) >= 10,
            F.col("probability") - 0.2,
        )
        .otherwise(F.col("probability")),
    )

    recommendations = recommendations.withColumn(
        "probability",
        F.when(
            F.col("user_city") == F.col("potential_friend_city"),
            F.col("probability") + 0.5,
        ).otherwise(F.col("probability")),
    )

    recommendations = recommendations.withColumn(
        "probability",
        F.when(
            (F.col("user_education") == 1) & (F.col("potential_friend_education") == 1),
            F.col("probability") + 0.3,
        )
        .when(
            (F.col("user_education") == 1) | (F.col("potential_friend_education") == 1),
            F.col("probability") + 0.1,
        )
        .otherwise(F.col("probability")),
    )

    recommendations = recommendations.withColumn(
        "probability",
        F.when(F.col("probability") > 1, 1)
        .when(F.col("probability") < 0, 0)
        .otherwise(F.col("probability")),
    )

    return recommendations
