# app_info_manager.py

class AppInfo:
    """
    내우약 앱의 홍보 정보를 관리하는 클래스입니다.
    """
    def __init__(self, description: str = "", pr_points: str = ""):
        self._description = description
        self._pr_points = pr_points

    @property
    def description(self) -> str:
        """앱 설명을 반환합니다."""
        return self._description

    @description.setter
    def description(self, value: str):
        """앱 설명을 설정합니다. (최소 50자, 최대 1000자)"""
        if not isinstance(value, str):
            raise TypeError("Description must be a string.")
        if not (50 <= len(value) <= 1000):
            raise ValueError("Description length must be between 50 and 1000 characters.")
        self._description = value

    @property
    def pr_points(self) -> str:
        """홍보 포인트를 반환합니다."""
        return self._pr_points

    @pr_points.setter
    def pr_points(self, value: str):
        """홍보 포인트를 설정합니다. (최소 20자, 최대 2000자)"""
        if not isinstance(value, str):
            raise TypeError("PR points must be a string.")
        if not (20 <= len(value) <= 2000):
            raise ValueError("PR points length must be between 20 and 2000 characters.")
        self._pr_points = value

    def load_from_dict(self, data: dict):
        """딕셔너리에서 앱 정보를 로드합니다."""
        if "description" in data:
            self.description = data["description"]
        if "pr_points" in data:
            self.pr_points = data["pr_points"]

    def to_dict(self) -> dict:
        """앱 정보를 딕셔너리로 반환합니다."""
        return {
            "description": self.description,
            "pr_points": self.pr_points
        }

    def __str__(self):
        return (f"App Description:\n{self.description}\n\n"
                f"PR Points:\n{self.pr_points}")

if __name__ == '__main__':
    # Example Usage
    print("--- AppInfo Class Example ---")

    # Create an instance with initial data
    app_details = AppInfo(
        description="내우약 앱은 가정 상비약의 유효기간을 관리하고, 영양제 복용 알림을 제공하는 스마트 건강 관리 애플리케이션입니다. 이 앱은 사용자들에게 편리하고 효율적인 건강 관리 경험을 제공합니다.",
        pr_points="1. 직관적인 유효기간 관리: 잊기 쉬운 상비약 유효기간을 쉽게 추적하고 알림.\n2. 맞춤형 영양제 알림: 개인별 복용 스케줄에 맞춰 영양제 복용 알림 제공.\n3. 가족 건강 관리: 여러 가족 구성원의 상비약 및 영양제 정보를 한곳에서 관리."
    )
    print(app_details)

    # Modify data with valid length
    try:
        app_details.description = "업데이트된 내우약 앱 설명입니다. 이 설명은 최소 길이 50자를 만족하도록 충분히 길게 작성되었습니다."
        print("\n--- After Description Update (Valid) ---")
        print(app_details.description)
    except ValueError as e:
        print(f"\n--- After Description Update (Invalid) ---")
        print(f"Caught unexpected error for valid description update: {e}")


    # Load from dictionary
    new_data = {
        "description": "새롭게 로드된 앱 설명입니다. 이 설명은 최소 길이 50자를 만족하도록 충분히 길게 작성되었습니다.",
        "pr_points": "새로운 홍보 포인트 1.\n새로운 홍보 포인트 2. 이 홍보 포인트는 최소 길이 20자를 만족합니다."
    }
    try:
        app_details.load_from_dict(new_data)
        print("\n--- After Loading from Dictionary ---")
        print(app_details)
    except ValueError as e:
        print(f"\n--- After Loading from Dictionary (Invalid) ---")
        print(f"Caught unexpected error for valid dictionary load: {e}")

    # Convert to dictionary
    dict_data = app_details.to_dict()
    print("\n--- Converted to Dictionary ---")
    print(dict_data)

    # Test validation (expected failures)
    print("\n--- Testing Validation (Expected Failures) ---")
    try:
        app_details.description = "too short"
    except ValueError as e:
        print(f"Caught expected error for short description: {e}")

    try:
        app_details.pr_points = "short"
    except ValueError as e:
        print(f"Caught expected error for short PR points: {e}")

    try:
        long_description = "a" * 1001
        app_details.description = long_description
    except ValueError as e:
        print(f"Caught expected error for long description: {e}")

    try:
        long_pr_points = "b" * 2001
        app_details.pr_points = long_pr_points
    except ValueError as e:
        print(f"Caught expected error for long PR points: {e}")

    # Test valid inputs after errors
    try:
        app_details.description = "이것은 유효성 검사를 통과하는 충분히 긴 앱 설명입니다. 최소 길이 50자를 만족합니다."
        print(f"\nSuccessfully set valid description: {app_details.description}")
    except ValueError as e:
        print(f"\nFailed to set valid description: {e}")

    try:
        app_details.pr_points = "이것은 유효성 검사를 통과하는 충분히 긴 홍보 포인트입니다. 최소 길이 20자를 만족합니다."
        print(f"Successfully set valid PR points: {app_details.pr_points}")
    except ValueError as e:
        print(f"Failed to set valid PR points: {e}")
