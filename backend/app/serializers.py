from rest_framework import serializers


class FormSerializer(serializers.Serializer):
    usn = serializers.CharField(max_length=7)
    range = serializers.CharField(max_length=100)
    url = serializers.URLField()

    def validate(self, data):
        """Validate USN structure and extract batch/branch."""
        usn = data["usn"].upper()
        if len(usn) != 7 or not usn[:3].isalnum() or not usn[3:5].isdigit() or not usn[5:7].isalpha():
            raise serializers.ValidationError(
                "Invalid USN. Use format like '1AB21CS' (7 characters)."
            )

        try:
            data["batch_year"] = "20" + usn[3:5]
            data["branch_code"] = usn[5:7]
        except IndexError:
            raise serializers.ValidationError("Invalid USN structure.")

        # Basic range validation
        range_str = data["range"]
        if not all(
            part.replace("-", "").isdigit() or "-" in part and len(part.split("-")) == 2
            for part in range_str.split(",")
        ):
            raise serializers.ValidationError(
                "Invalid range. Use format like '1-100,150'."
            )

        return data