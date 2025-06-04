import pytest
from unittest.mock import MagicMock, patch
from services.social_service import SocialService
from models.meal import Meal
from models.post import Post
from models.comment import Comment
from schemas.meal_recommendation import MealRecommendationResponse
from schemas.comment import CommentResponse
from schemas.like import LikeResponse
from RL.utils_model.calories_config import CALORIE_RANGES
from datetime import datetime, timedelta

pytestmark = pytest.mark.asyncio

class TestSocialService:

    def setup_method(self):
        self.user_repo = MagicMock()
        self.post_repo = MagicMock()
        self.friendship_repo = MagicMock()
        self.meal_repo = MagicMock()
        self.meal_rec_repo = MagicMock()

        self.service = SocialService.__new__(SocialService)  # Bypassează __init__
        self.service.user_repo = self.user_repo
        self.service.post_repo = self.post_repo
        self.service.friendship_repo = self.friendship_repo
        self.service.meal_repo = self.meal_repo
        self.service.meal_recommendation_repo = self.meal_rec_repo
        self.service.db = MagicMock()  # optional

    def test_invalid_profile(self):
        with pytest.raises(ValueError, match="Invalid profile"):
            self.service.get_meal_recommendations(user_id=1, profile="invalid", target_calories=2000)

    def test_invalid_calories_for_profile(self):
        profile = list(CALORIE_RANGES.keys())[0]
        invalid_cal = 99999
        with pytest.raises(ValueError, match="Invalid calorie target"):
            self.service.get_meal_recommendations(user_id=1, profile=profile, target_calories=invalid_cal)

    @patch("services.social_service.recommend_meals")
    def test_no_recommendations(self, mock_recommend):
        profile = list(CALORIE_RANGES.keys())[0]
        target = CALORIE_RANGES[profile][0]
        mock_recommend.return_value = []

        with pytest.raises(ValueError, match="No recommendations available"):
            self.service.get_meal_recommendations(user_id=1, profile=profile, target_calories=target)

    @patch("services.social_service.recommend_meals")
    def test_successful_recommendation(self, mock_recommend):
        profile = list(CALORIE_RANGES.keys())[0]
        target = CALORIE_RANGES[profile][0]

        meal = Meal(
            id=1,
            name="Oatmeal",
            calories=300,
            protein=10,
            carbs=40,
            fats=5,
            photo_url="http://localhost/image.jpg",
            ingredients='["oats","milk"]'
        )
        mock_recommend.return_value = [meal]

        saved_rec = MagicMock()
        saved_rec.id = 123
        saved_rec.user_id = 1
        saved_rec.profile_type = profile
        saved_rec.target_calories = target
        saved_rec.meals = [meal]

        self.service.meal_recommendation_repo.create_recommendation = MagicMock(return_value=saved_rec)

        response = self.service.get_meal_recommendations(user_id=1, profile=profile, target_calories=target)

        assert isinstance(response, MealRecommendationResponse)
        assert response.id == 123

    def test_get_user_nutrition_statistics(self):
        # setup
        today = datetime.now().date()
        mock_post = MagicMock()
        mock_post.created_at = datetime.now()
        mock_post.macros = {'calories': 900, 'protein': 30, 'carbs': 80, 'fats': 20}
        self.service.post_repo.get_user_posts_in_range.return_value = [mock_post]

        result = self.service.get_user_nutrition_statistics(
            user_id=1,
            start_date=today.isoformat(),
            end_date=today.isoformat()
        )

        assert result.total_days_considered == 1
        assert result.average_calories == 900
        assert round(result.protein_distribution + result.carbs_distribution + result.fats_distribution, 1) == 100.0

    def test_register_user_email_taken(self):
        self.service.user_repo.get_user_by_email.return_value = MagicMock()
        with pytest.raises(ValueError, match="User with this email already exists"):
            self.service.register_user("george", "g@g.com", "pass123", file=None)

    def test_register_user_username_taken(self):
        self.service.user_repo.get_user_by_email.return_value = None
        self.service.user_repo.get_user_by_username.return_value = MagicMock()
        with pytest.raises(ValueError, match="Username already taken"):
            self.service.register_user("george", "g@g.com", "pass123", file=None)

    @pytest.mark.asyncio
    async def test_comment_on_post_limit_exceeded(self):
        mock_post = MagicMock()
        mock_post.user_id = 1  # 👈 Permite accesul
        mock_post.comments = [MagicMock(user_id=1), MagicMock(user_id=1), MagicMock(user_id=1)]
        self.service.post_repo.get_post_by_id.return_value = mock_post
        self.service.friendship_repo.get_friends.return_value = []

        with pytest.raises(ValueError, match="only comment up to 3"):
            await self.service.comment_on_post(user_id=1, post_id=1, text="Nice post!")

    @pytest.mark.asyncio
    async def test_like_post_success(self):
        mock_post = MagicMock()
        mock_post.user_id = 1  # 👈 Necesare pentru acces
        self.service.post_repo.get_post_by_id.return_value = mock_post
        self.service.friendship_repo.get_friends.return_value = []

        mock_like = MagicMock(id=1, user_id=1, post_id=2)
        self.service.post_repo.add_like.return_value = mock_like

        response = await self.service.like_post(user_id=1, post_id=2)
        assert isinstance(response, LikeResponse)
        assert response.user_id == 1
        assert response.post_id == 2

    def test_get_post_by_id_success(self):
        mock_post = MagicMock()
        mock_post.id = 10
        mock_post.user_id = 1
        mock_post.caption = "test caption"
        mock_post.image_url = "/image.jpg"
        mock_post.macros = {"calories": 300}
        mock_post.likes = []
        mock_post.comments = []

        self.post_repo.get_post_by_id.return_value = mock_post
        self.user_repo.get_user_by_id.return_value.username = "tester"

        response = self.service.get_post_by_id(post_id=10)

        assert response.id == 10
        assert response.caption == "test caption"
        assert str(response.image_url) == "http://localhost:8000/image.jpg"


    def test_get_user_posts_none_found(self):
        self.post_repo.get_posts_by_user.return_value = []

        with pytest.raises(ValueError, match="No posts found"):
            self.service.get_user_posts(user_id=1)

    def test_delete_meal_recommendation_success(self):
        self.meal_rec_repo.delete_recommendation.return_value = True

        response = self.service.delete_meal_recommendation(user_id=1, recommendation_id=100)
        assert response == {"message": "Meal recommendation deleted successfully"}

    def test_delete_meal_recommendation_not_found(self):
        self.meal_rec_repo.delete_recommendation.return_value = False

        with pytest.raises(ValueError, match="not found for user"):
            self.service.delete_meal_recommendation(user_id=1, recommendation_id=100)

    def test_get_username_by_id_success(self):
        mock_user = MagicMock()
        mock_user.username = "george"
        self.user_repo.get_user_by_id.return_value = mock_user

        result = self.service.get_username_by_id(user_id=1)
        assert result == "george"

    def test_get_username_by_id_not_found(self):
        self.user_repo.get_user_by_id.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            self.service.get_username_by_id(user_id=99)

    def test_search_users_called(self):
        self.user_repo.search_users.return_value = ["mocked_result"]
        result = self.service.search_users("geo")

        self.user_repo.search_users.assert_called_once_with("geo")
        assert result == ["mocked_result"]

    def test_view_pending_requests(self):
        self.friendship_repo.get_pending_requests.return_value = ["req1", "req2"]
        result = self.service.view_pending_requests(1)
        assert result == ["req1", "req2"]

    def test_view_friends(self):
        self.friendship_repo.get_friends.return_value = ["friendA"]
        result = self.service.view_friends(1)
        assert result == ["friendA"]

    def test_view_sent_requests(self):
        self.friendship_repo.get_sent_pending_requests.return_value = ["sent1"]
        result = self.service.view_sent_requests(1)
        assert result == ["sent1"]

    @pytest.mark.asyncio
    async def test_accept_friend_request_success(self):
        friendship = MagicMock()
        friendship.receiver_id = 1
        friendship.status = "pending"

        self.friendship_repo.get_friendship_by_id.return_value = friendship

        result = await self.service.accept_friend_request(request_id=10, user_id=1)

        assert result.status == "accepted"
        self.service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_accept_friend_request_invalid_user(self):
        friendship = MagicMock()
        friendship.receiver_id = 2  # not current user
        friendship.status = "pending"
        self.friendship_repo.get_friendship_by_id.return_value = friendship

        with pytest.raises(ValueError, match="not meant for you"):
            await self.service.accept_friend_request(request_id=10, user_id=1)

    @pytest.mark.asyncio
    async def test_accept_friend_request_already_accepted(self):
        friendship = MagicMock()
        friendship.receiver_id = 1
        friendship.status = "accepted"
        self.friendship_repo.get_friendship_by_id.return_value = friendship

        with pytest.raises(ValueError, match="already accepted or rejected"):
            await self.service.accept_friend_request(request_id=10, user_id=1)

    def test_reject_friend_request_success(self):
        friendship = MagicMock()
        friendship.receiver_id = 1
        self.friendship_repo.get_friendship_by_id.return_value = friendship

        msg = self.service.reject_friend_request(request_id=5, user_id=1)

        assert msg == "Friend request rejected and removed"
        self.service.db.delete.assert_called_once_with(friendship)
        self.service.db.commit.assert_called_once()

    def test_reject_friend_request_not_found(self):
        self.friendship_repo.get_friendship_by_id.return_value = None

        with pytest.raises(ValueError, match="Friend request not found"):
            self.service.reject_friend_request(request_id=5, user_id=1)

    def test_get_user_feed_no_friends(self):
        self.friendship_repo.get_friends.return_value = []
        result = self.service.get_user_feed(user_id=1)
        assert result == []

    def test_get_user_feed_with_friends(self):
        friend_obj = MagicMock(sender_id=1, receiver_id=2)
        self.friendship_repo.get_friends.return_value = [friend_obj]

        post = MagicMock()
        post.id = 10
        post.user_id = 2
        post.caption = "test post"
        post.image_url = "/image.jpg"
        post.macros = {"calories": 500}
        post.likes = []
        post.comments = []
        self.post_repo.get_posts_by_user_ids.return_value = [post]
        self.user_repo.get_user_by_id.return_value.username = "friend"

        result = self.service.get_user_feed(user_id=1)

        assert len(result) == 1
        assert result[0].username == "friend"
        assert result[0].caption == "test post"

    @pytest.mark.asyncio
    async def test_unlike_post_success(self):
        mock_post = MagicMock()
        mock_post.user_id = 1
        self.post_repo.get_post_by_id.return_value = mock_post
        self.friendship_repo.get_friends.return_value = []
        self.post_repo.get_like.return_value = MagicMock()

        result = await self.service.unlike_post(user_id=1, post_id=20)
        assert result["message"] == "Like removed successfully"
        self.post_repo.remove_like.assert_called_once_with(1, 20)

    @pytest.mark.asyncio
    async def test_unlike_post_not_liked(self):
        mock_post = MagicMock()
        mock_post.user_id = 1
        self.post_repo.get_post_by_id.return_value = mock_post
        self.friendship_repo.get_friends.return_value = []
        self.post_repo.get_like.return_value = None

        with pytest.raises(ValueError, match="haven't liked this post"):
            await self.service.unlike_post(user_id=1, post_id=20)


    @pytest.mark.asyncio
    async def test_comment_on_post_success(self):
        mock_post = MagicMock()
        mock_post.user_id = 1
        mock_post.comments = [MagicMock(user_id=2)]  # nu-s comentariile lui user_id=1

        self.post_repo.get_post_by_id.return_value = mock_post
        self.friendship_repo.get_friends.return_value = []

        mock_comment = MagicMock()
        mock_comment.id = 10
        mock_comment.user_id = 1
        mock_comment.text = "Great!"
        mock_comment.created_at = datetime.now()
        self.post_repo.add_comment.return_value = mock_comment
        self.user_repo.get_user_by_id.return_value.username = "george"

        response = await self.service.comment_on_post(user_id=1, post_id=1, text="Great!")
        assert response.text == "Great!"
        assert response.username == "george"

    def test_get_comments_success(self):
        mock_post = MagicMock()
        mock_post.user_id = 1
        self.post_repo.get_post_by_id.return_value = mock_post
        self.friendship_repo.get_friends.return_value = []

        expected_comments = [MagicMock(), MagicMock()]
        self.post_repo.get_comments_for_post.return_value = expected_comments

        comments = self.service.get_comments(user_id=1, post_id=5)
        assert comments == expected_comments

    def test_register_user_success(self):
        self.user_repo.get_user_by_email.return_value = None
        self.user_repo.get_user_by_username.return_value = None

        new_user = MagicMock(id=1)
        self.user_repo.create_user.return_value = new_user

        mock_file = MagicMock()
        mock_file.filename = "pic.jpg"
        mock_file.file.read.return_value = b"data"
        mock_file.file.tell.return_value = 1024
        mock_file.file.seek.side_effect = lambda *args: None

        self.service._save_profile_picture = MagicMock(return_value="http://localhost:8000/profile_pictures/1.jpg")

        user = self.service.register_user("george", "g@g.com", "pw123", file=mock_file)

        assert user.profile_picture.endswith(".jpg")
        self.service.db.commit.assert_called_once()

    def test_validate_file_success(self):
        mock_file = MagicMock()
        mock_file.filename = "image.png"
        mock_file.file.tell.return_value = 1024
        mock_file.file.seek.side_effect = lambda *args: None

        try:
            self.service._validate_file(mock_file)
        except Exception:
            pytest.fail("Should not raise exception for valid file")

    def test_validate_file_invalid_format(self):
        mock_file = MagicMock()
        mock_file.filename = "image.gif"

        with pytest.raises(ValueError, match="Invalid file format"):
            self.service._validate_file(mock_file)

    def test_validate_file_too_large(self):
        mock_file = MagicMock()
        mock_file.filename = "image.jpg"
        mock_file.file.tell.return_value = 3 * 1024 * 1024  # 3MB
        mock_file.file.seek.side_effect = lambda *args: None

        with pytest.raises(ValueError, match="File size must be less than 2MB"):
            self.service._validate_file(mock_file)

    def test_remove_friend_calls_update(self):
        self.friendship_repo.update_friendship_status.return_value = "updated"
        result = self.service.remove_friend(friendship_id=42)
        assert result == "updated"

    def test_delete_friend_calls_delete(self):
        self.service.delete_friend(friendship_id=42)
        self.friendship_repo.delete_friendship.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_send_friend_request_self(self):
        with pytest.raises(ValueError, match="cannot send a friend request to yourself"):
            await self.service.send_friend_request(sender_id=1, receiver_id=1)

    @pytest.mark.asyncio
    async def test_send_friend_request_already_friends(self):
        existing = MagicMock(status="accepted")
        self.friendship_repo.get_friendship.return_value = existing

        with pytest.raises(ValueError, match="already friends"):
            await self.service.send_friend_request(sender_id=1, receiver_id=2)

    @pytest.mark.asyncio
    async def test_send_friend_request_pending(self):
        existing = MagicMock(status="pending")
        self.friendship_repo.get_friendship.return_value = existing

        with pytest.raises(ValueError, match="already sent"):
            await self.service.send_friend_request(sender_id=1, receiver_id=2)

    @pytest.mark.asyncio
    async def test_send_friend_request_rejected_deleted_and_created(self):
        existing = MagicMock(status="rejected", id=99)
        self.friendship_repo.get_friendship.return_value = existing
        self.friendship_repo.create_friend_request.return_value = "created"

        self.friendship_repo.delete_friendship = MagicMock()
        result = await self.service.send_friend_request(sender_id=1, receiver_id=2)

        self.friendship_repo.delete_friendship.assert_called_once_with(99)
        assert result == "created"

    @pytest.mark.asyncio
    async def test_send_friend_request_success_no_existing(self):
        self.friendship_repo.get_friendship.return_value = None
        self.friendship_repo.create_friend_request.return_value = "new_req"

        result = await self.service.send_friend_request(sender_id=1, receiver_id=2)
        assert result == "new_req"

    def test_save_post_image_creates_file(self, tmp_path, monkeypatch):
        mock_file = MagicMock()
        mock_file.filename = "photo.jpg"
        mock_file.file = MagicMock()
        mock_file.file.tell.return_value = 1024  # 🟢 mock corect
        mock_file.file.seek.side_effect = lambda *args: None

        monkeypatch.setattr("shutil.copyfileobj", lambda src, dst: None)

        result = self.service.save_post_image(user_id=5, file=mock_file)
        assert result.startswith("/post_pictures/5_")
        assert result.endswith(".jpg")

    def test_get_user_posts_success(self):
        post = MagicMock()
        post.id = 1
        post.user_id = 1
        post.caption = "My post"
        post.image_url = "/image.jpg"
        post.macros = {"calories": 250}
        post.likes = []
        post.comments = []
        post.created_at = datetime.now()

        self.post_repo.get_posts_by_user.return_value = [post]
        self.user_repo.get_user_by_id.return_value.username = "george"

        result = self.service.get_user_posts(user_id=1)
        assert len(result) == 1
        assert result[0].caption == "My post"
        assert result[0].username == "george"

    def test_save_profile_picture(self, monkeypatch, tmp_path):
        mock_file = MagicMock()
        mock_file.filename = "avatar.png"
        mock_file.file = MagicMock()

        monkeypatch.setattr(self.service, "_validate_file", lambda x: None)
        monkeypatch.setattr("os.path.exists", lambda path: False)
        monkeypatch.setattr("shutil.copyfileobj", lambda src, dst: None)

        result = self.service._save_profile_picture(user_id=2, file=mock_file)
        assert result == "http://localhost:8000/profile_pictures/2.png"

    def test_get_user_meal_recommendations_success(self):
        meal = MagicMock()
        meal.id = 1
        meal.name = "Chicken"
        meal.calories = 300
        meal.protein = 30
        meal.carbs = 10
        meal.fats = 10
        meal.photo_url = "http://localhost/chicken.jpg"
        meal.ingredients = '["chicken", "rice"]'

        rec = MagicMock()
        rec.id = 7
        rec.user_id = 1
        rec.profile_type = "omnivore"
        rec.target_calories = 1800
        rec.meals = [meal]

        self.meal_rec_repo.get_user_recommendations.return_value = [rec]

        response = self.service.get_user_meal_recommendations(user_id=1)
        assert len(response) == 1
        assert response[0].meals[0].name == "Chicken"

    @pytest.mark.asyncio
    async def test_create_user_post_with_image(self, monkeypatch):
        mock_file = MagicMock()
        mock_file.filename = "image.jpg"
        mock_file.file.tell.return_value = 1024
        mock_file.file.seek.side_effect = lambda *args: None

        monkeypatch.setattr(self.service, "_validate_file", lambda x: None)
        monkeypatch.setattr("shutil.copyfileobj", lambda src, dst: None)
        monkeypatch.setattr("uuid.uuid4", lambda: MagicMock(hex="abc123"))

        mock_post = MagicMock()
        mock_post.id = 10
        mock_post.user_id = 1
        mock_post.user.username = "george"
        mock_post.caption = "caption"
        mock_post.image_url = f"/post_pictures/1_abc123.jpg"
        mock_post.macros = {"calories": 100}
        mock_post.likes = []
        mock_post.comments = []
        mock_post.created_at = datetime.now()
        self.post_repo.create_post.return_value = mock_post
        self.friendship_repo.get_friends.return_value = []

        response = await self.service.create_user_post(
            user_id=1,
            caption="caption",
            file=mock_file,
            macros={"calories": 100}
        )

        assert response.caption == "caption"
        assert str(response.image_url) == "http://localhost:8000/post_pictures/1_abc123.jpg"

    @patch("services.social_service.verify_password")
    def test_authenticate_user_success(self, mock_verify):
        mock_user = MagicMock()
        mock_user.password_hash = "hashed"
        self.user_repo.get_user_by_email.return_value = mock_user
        mock_verify.return_value = True

        result = self.service.authenticate_user(email="test@example.com", password="secret")
        assert result == mock_user

    @patch("services.social_service.verify_password")
    def test_authenticate_user_invalid_email(self, mock_verify):
        self.user_repo.get_user_by_email.return_value = None
        mock_verify.return_value = False

        with pytest.raises(ValueError, match="Invalid credentials"):
            self.service.authenticate_user(email="x", password="x")

    @patch("services.social_service.verify_password")
    def test_authenticate_user_invalid_password(self, mock_verify):
        mock_user = MagicMock()
        mock_user.password_hash = "wrong"
        self.user_repo.get_user_by_email.return_value = mock_user
        mock_verify.return_value = False

        with pytest.raises(ValueError, match="Invalid credentials"):
            self.service.authenticate_user(email="x", password="wrong")

    def test_save_meal_recommendation_success(self):
        self.meal_rec_repo.create_recommendation.return_value = "saved"

        result = self.service.save_meal_recommendation(
            user_id=1,
            profile_type="vegan",
            target_calories=1500,
            meal_ids=[1, 2, 3]
        )

        self.meal_rec_repo.create_recommendation.assert_called_once_with(1, "vegan", 1500, [1, 2, 3])
        assert result == "saved"

    def test_calculate_averages_empty_input(self):
        result = self.service._calculate_averages([])
        assert result == {
            "average_calories": 0,
            "average_protein": 0,
            "average_carbs": 0,
            "average_fats": 0,
            "total_days_considered": 0
        }

    def test_calculate_distribution_all_zero(self):
        input_days = [{"protein": 0, "carbs": 0, "fats": 0}]
        result = self.service._calculate_distribution(input_days)
        assert result == {
            "protein_distribution": 0.0,
            "carbs_distribution": 0.0,
            "fats_distribution": 0.0
        }

    def test_get_user_by_id_success(self):
        mock_user = MagicMock()
        self.user_repo.get_user_by_id.return_value = mock_user

        result = self.service.get_user_by_id(1)
        self.user_repo.get_user_by_id.assert_called_once_with(1)
        assert result == mock_user

    def test_calculate_distribution_empty_list(self):
        result = self.service._calculate_distribution([])
        assert result == {
            "protein_distribution": 0.0,
            "carbs_distribution": 0.0,
            "fats_distribution": 0.0
        }

    @pytest.mark.asyncio
    async def test_comment_on_post_empty_text(self):
        mock_post = MagicMock()
        mock_post.user_id = 1
        mock_post.comments = []
        self.service.post_repo.get_post_by_id.return_value = mock_post
        self.service.friendship_repo.get_friends.return_value = []

        with pytest.raises(ValueError, match="Comment cannot be empty"):
            await self.service.comment_on_post(user_id=1, post_id=1, text="   ")

    def test_calculate_distribution_real_values(self):
        days = [{"protein": 25, "carbs": 50, "fats": 20}]
        result = self.service._calculate_distribution(days)

        assert round(result["protein_distribution"], 1) == 20.8
        assert round(result["carbs_distribution"], 1) == 41.7
        assert round(result["fats_distribution"], 1) == 37.5

    def test_get_user_nutrition_statistics_multiple_days(self):
        day1 = MagicMock()
        day1.created_at = datetime.now()
        day1.macros = {'calories': 900, 'protein': 30, 'carbs': 70, 'fats': 20}

        day2 = MagicMock()
        day2.created_at = datetime.now() - timedelta(days=1)
        day2.macros = {'calories': 1000, 'protein': 40, 'carbs': 80, 'fats': 30}

        self.service.post_repo.get_user_posts_in_range.return_value = [day1, day2]

        result = self.service.get_user_nutrition_statistics(
            user_id=1,
            start_date=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )

        assert result.total_days_considered == 2
        assert round(result.average_calories, 1) == 950.0



    def test_get_post_by_id_with_comments_and_likes(self):
        mock_post = MagicMock()
        mock_post.id = 10
        mock_post.user_id = 1
        mock_post.caption = "test"
        mock_post.image_url = "/image.jpg"
        mock_post.macros = {"calories": 100}
        mock_post.likes = [MagicMock(id=1, user_id=2, post_id=10)]
        mock_post.comments = [MagicMock(id=1, user_id=2, post_id=10, text="Nice!", created_at=datetime.now())]

        self.post_repo.get_post_by_id.return_value = mock_post
        self.user_repo.get_user_by_id.return_value.username = "john"

        response = self.service.get_post_by_id(post_id=10)

        assert len(response.likes) == 1
        assert len(response.comments) == 1
        assert response.comments[0].username == "john"


    @patch("services.social_service.recommend_meals")
    def test_get_meal_recommendations_with_dict_ingredients(self, mock_recommend):
        profile = "omnivore"
        target = CALORIE_RANGES[profile][0]

        meal = MagicMock()
        meal.id = 1
        meal.name = "Meal"
        meal.calories = 400
        meal.protein = 30
        meal.carbs = 50
        meal.fats = 10
        meal.photo_url = "http://img.jpg"
        meal.ingredients = ["rice", "chicken"]

        mock_recommend.return_value = [meal]

        saved = MagicMock()
        saved.id = 5
        saved.user_id = 1
        saved.profile_type = profile
        saved.target_calories = target
        saved.meals = [meal]

        self.service.meal_recommendation_repo.create_recommendation.return_value = saved

        result = self.service.get_meal_recommendations(user_id=1, profile=profile, target_calories=target)
        assert isinstance(result, MealRecommendationResponse)
        assert result.meals[0].ingredients == ["rice", "chicken"]




