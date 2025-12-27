"""
Tests for RIVET Telegram Onboarding System

Tests cover:
- API key authentication
- Multi-step onboarding flow
- Feature tour navigation
- Skip functionality
- Resume partial onboarding
- Tier-specific messaging
- Quick reference generation

Created: 2025-12-27
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User, Message, CallbackQuery, Chat
from telegram.ext import ContextTypes

from agent_factory.integrations.telegram.onboarding_manager import OnboardingManager
from agent_factory.integrations.telegram.feature_tour import FeatureTour
from agent_factory.integrations.telegram.quick_reference import (
    get_quickstart_message,
    get_help_message,
    get_about_message,
    get_tier_comparison
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database for testing"""
    db = Mock()
    db.get_user_by_telegram_id = AsyncMock(return_value={
        "user_id": "test_user_123",
        "telegram_id": "12345",
        "subscription_tier": "beta",
        "onboarding_completed": False,
        "onboarding_step": 0,
        "onboarding_skipped": False
    })
    db.update_user = AsyncMock()
    db.link_telegram_id = AsyncMock()
    return db


@pytest.fixture
def mock_update():
    """Mock Telegram update"""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"

    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()

    update.callback_query = None

    return update


@pytest.fixture
def mock_context():
    """Mock Telegram context"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.user_data = {}
    return context


@pytest.fixture
def onboarding_manager(mock_db):
    """Create OnboardingManager instance"""
    return OnboardingManager(db=mock_db)


@pytest.fixture
def feature_tour():
    """Create FeatureTour instance"""
    return FeatureTour()


# ============================================================================
# OnboardingManager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_start_onboarding_new_user(onboarding_manager, mock_update, mock_context, mock_db):
    """Test onboarding flow for new user"""
    user_data = {
        "user_id": "test_user_123",
        "subscription_tier": "beta",
        "onboarding_completed": False,
        "onboarding_step": 0
    }

    await onboarding_manager.start_onboarding(mock_update, mock_context, user_data)

    # Should call reply_text with welcome message
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args
    assert "Welcome to RIVET Beta!" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_start_onboarding_returning_user(onboarding_manager, mock_update, mock_context, mock_db):
    """Test onboarding flow for returning user who completed onboarding"""
    user_data = {
        "user_id": "test_user_123",
        "subscription_tier": "pro",
        "onboarding_completed": True,
        "onboarding_step": 5
    }

    await onboarding_manager.start_onboarding(mock_update, mock_context, user_data)

    # Should show welcome back message
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args
    assert "Welcome back to RIVET!" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_api_key_authentication_valid(onboarding_manager, mock_update, mock_context, mock_db):
    """Test API key authentication with valid key"""
    with patch.object(onboarding_manager.api_client, 'validate_api_key', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {
            "user_id": "api_user_456",
            "email": "test@example.com",
            "subscription_tier": "pro"
        }

        mock_db.get_user_by_telegram_id.return_value = {
            "user_id": "api_user_456",
            "subscription_tier": "pro",
            "onboarding_completed": False,
            "onboarding_step": 0
        }

        await onboarding_manager.authenticate_with_api_key(
            mock_update,
            mock_context,
            "sk_rivet_abc123"
        )

        # Should validate API key
        mock_validate.assert_called_once_with("sk_rivet_abc123")

        # Should link Telegram ID
        mock_db.link_telegram_id.assert_called_once()

        # Should store in context
        assert context.user_data.get("api_key") == "sk_rivet_abc123"


@pytest.mark.asyncio
async def test_api_key_authentication_invalid(onboarding_manager, mock_update, mock_context, mock_db):
    """Test API key authentication with invalid key"""
    with patch.object(onboarding_manager.api_client, 'validate_api_key', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None  # Invalid key

        await onboarding_manager.authenticate_with_api_key(
            mock_update,
            mock_context,
            "sk_rivet_invalid"
        )

        # Should show error message
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args
        assert "Invalid API Key" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_skip_onboarding(onboarding_manager, mock_update, mock_context, mock_db):
    """Test skipping onboarding tutorial"""
    user_data = {
        "user_id": "test_user_123",
        "subscription_tier": "beta",
        "onboarding_completed": False,
        "onboarding_step": 2
    }

    # Mock callback query
    mock_update.callback_query = Mock(spec=CallbackQuery)
    mock_update.callback_query.edit_message_text = AsyncMock()

    await onboarding_manager.skip_onboarding(mock_update, user_data)

    # Should mark as skipped in database
    mock_db.update_user.assert_called_once()
    call_args = mock_db.update_user.call_args
    assert call_args[1]["updates"]["onboarding_skipped"] == True


@pytest.mark.asyncio
async def test_resume_onboarding(onboarding_manager, mock_update, mock_context, mock_db):
    """Test resuming partial onboarding"""
    user_data = {
        "user_id": "test_user_123",
        "subscription_tier": "beta",
        "onboarding_completed": False,
        "onboarding_step": 3  # Left off at step 3
    }

    await onboarding_manager.resume_onboarding(mock_update, mock_context, user_data, step=3)

    # Should show resume message
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args
    assert "Welcome back!" in call_args[1]["text"]
    assert "Step 3" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_complete_onboarding(onboarding_manager, mock_db):
    """Test marking onboarding as complete"""
    telegram_id = "12345"

    await onboarding_manager.complete_onboarding(telegram_id)

    # Should update database
    mock_db.update_user.assert_called_once()
    call_args = mock_db.update_user.call_args
    assert call_args[1]["updates"]["onboarding_completed"] == True
    assert call_args[1]["updates"]["onboarding_step"] == 5


@pytest.mark.asyncio
async def test_tier_welcome_messages(onboarding_manager):
    """Test tier-specific welcome messages"""
    # Beta tier
    beta_message = onboarding_manager.get_tier_welcome_message("beta")
    assert "Welcome to RIVET Beta!" in beta_message
    assert "5 AI-powered troubleshooting questions/day" in beta_message

    # Pro tier
    pro_message = onboarding_manager.get_tier_welcome_message("pro")
    assert "Welcome to RIVET Pro!" in pro_message
    assert "UNLIMITED troubleshooting questions" in pro_message

    # Enterprise/Team tier
    team_message = onboarding_manager.get_tier_welcome_message("team")
    assert "Welcome to RIVET Enterprise!" in team_message
    assert "10 team members" in team_message


# ============================================================================
# FeatureTour Tests
# ============================================================================

@pytest.mark.asyncio
async def test_feature_tour_menu(feature_tour, mock_update):
    """Test feature tour menu display"""
    user_data = {"subscription_tier": "beta"}

    await feature_tour.show_tour_menu(mock_update, user_data)

    # Should display tour menu
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args
    assert "RIVET Feature Tour" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_feature_tour_tier_filtering(feature_tour):
    """Test tier-specific feature visibility in tour"""
    # Beta user - basic features only
    beta_keyboard = feature_tour.get_tour_keyboard("beta")
    assert len(beta_keyboard.inline_keyboard) == 3  # Troubleshooting, Machine Library, Finish

    # Pro user - includes premium features
    pro_keyboard = feature_tour.get_tour_keyboard("pro")
    assert len(pro_keyboard.inline_keyboard) == 5  # + Field Eye, PDF Export

    # Team user - includes all features
    team_keyboard = feature_tour.get_tour_keyboard("team")
    assert len(team_keyboard.inline_keyboard) == 6  # + Team Management


@pytest.mark.asyncio
async def test_tour_navigation(feature_tour, mock_update, mock_context):
    """Test navigation through tour steps"""
    user_data = {"subscription_tier": "pro"}

    # Mock callback query
    mock_update.callback_query = Mock(spec=CallbackQuery)
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.callback_query.answer = AsyncMock()

    # Show troubleshooting tour
    await feature_tour.show_troubleshooting_tour(mock_update, mock_context)
    assert mock_update.callback_query.edit_message_text.called

    # Show machine lib tour
    await feature_tour.show_machine_lib_tour(mock_update, mock_context)
    assert mock_update.callback_query.edit_message_text.called


# ============================================================================
# QuickReference Tests
# ============================================================================

def test_quickstart_message_beta():
    """Test quick reference for beta tier"""
    message = get_quickstart_message("beta")

    assert "Quick Reference Card" in message
    assert "/troubleshoot" in message
    assert "/add_machine" in message
    # Should NOT have pro features
    assert "/book_expert" not in message


def test_quickstart_message_pro():
    """Test quick reference for pro tier"""
    message = get_quickstart_message("pro")

    assert "Quick Reference Card" in message
    assert "/book_expert" in message
    assert "/export_session" in message
    # Should NOT have team features
    assert "/team_dashboard" not in message


def test_quickstart_message_team():
    """Test quick reference for enterprise/team tier"""
    message = get_quickstart_message("team")

    assert "Quick Reference Card" in message
    assert "/book_expert" in message
    assert "/team_dashboard" in message
    assert "/team_invite" in message


def test_help_message_structure():
    """Test help message structure"""
    message = get_help_message("beta")

    assert "TROUBLESHOOTING" in message
    assert "MACHINE LIBRARY" in message
    assert "PRINTS & MANUALS" in message
    assert "HELP & LEARNING" in message


def test_about_message():
    """Test about message content"""
    message = get_about_message()

    assert "About RIVET" in message
    assert "1,964+ validated maintenance solutions" in message
    assert "Why Trust RIVET?" in message


def test_tier_comparison():
    """Test tier comparison table"""
    message = get_tier_comparison()

    assert "RIVET Pricing Tiers" in message
    assert "BETA" in message
    assert "PRO" in message
    assert "ENTERPRISE" in message


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_onboarding_flow(onboarding_manager, mock_update, mock_context, mock_db):
    """Test complete onboarding flow from start to finish"""
    user_data = {
        "user_id": "test_user_123",
        "subscription_tier": "beta",
        "onboarding_completed": False,
        "onboarding_step": 0
    }

    # Step 1: Start onboarding
    await onboarding_manager.start_onboarding(mock_update, mock_context, user_data)
    assert mock_update.message.reply_text.called

    # Step 2: Feature tour
    mock_update.callback_query = Mock(spec=CallbackQuery)
    mock_update.callback_query.edit_message_text = AsyncMock()
    await onboarding_manager.begin_step_2(mock_update, mock_context, user_data)
    assert mock_update.callback_query.edit_message_text.called

    # Step 3: First troubleshooting
    await onboarding_manager.begin_step_3(mock_update, mock_context, user_data)
    assert mock_update.callback_query.edit_message_text.called

    # Step 4: Machine library
    await onboarding_manager.begin_step_4(mock_update, mock_context, user_data)
    assert mock_update.callback_query.edit_message_text.called

    # Step 5: Completion
    await onboarding_manager.begin_step_5(mock_update, mock_context, user_data)
    assert mock_update.callback_query.edit_message_text.called

    # Should mark as complete
    mock_db.update_user.assert_called()


@pytest.mark.asyncio
async def test_onboarding_with_api_key_flow(onboarding_manager, mock_update, mock_context, mock_db):
    """Test onboarding flow starting with API key authentication"""
    with patch.object(onboarding_manager.api_client, 'validate_api_key', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {
            "user_id": "api_user_789",
            "email": "premium@example.com",
            "subscription_tier": "pro"
        }

        mock_db.get_user_by_telegram_id.return_value = {
            "user_id": "api_user_789",
            "subscription_tier": "pro",
            "onboarding_completed": False,
            "onboarding_step": 0
        }

        # Authenticate with API key
        await onboarding_manager.authenticate_with_api_key(
            mock_update,
            mock_context,
            "sk_rivet_premium_xyz"
        )

        # Should show authentication success
        calls = mock_update.message.reply_text.call_args_list
        assert any("Authenticated Successfully" in str(call) for call in calls)


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_onboarding_with_no_tier(onboarding_manager, mock_update, mock_context, mock_db):
    """Test onboarding with missing tier data"""
    user_data = {
        "user_id": "test_user_123",
        # Missing subscription_tier - should default to beta
        "onboarding_completed": False,
        "onboarding_step": 0
    }

    await onboarding_manager.start_onboarding(mock_update, mock_context, user_data)

    # Should still work and default to beta
    assert mock_update.message.reply_text.called


def test_quickstart_with_unknown_tier():
    """Test quick reference with unknown tier"""
    # Should fall back to beta tier
    message = get_quickstart_message("unknown_tier")

    assert "Quick Reference Card" in message
    # Should not have pro/team features
    assert "/book_expert" not in message
    assert "/team_dashboard" not in message


@pytest.mark.asyncio
async def test_update_onboarding_step(onboarding_manager, mock_db):
    """Test updating onboarding step in database"""
    telegram_id = "12345"

    await onboarding_manager.update_onboarding_step(telegram_id, step=3)

    # Should call database update
    mock_db.update_user.assert_called_once()
    call_args = mock_db.update_user.call_args
    assert call_args[1]["updates"]["onboarding_step"] == 3
