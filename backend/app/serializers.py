from rest_framework import serializers

class FormSerializer(serializers.Serializer):
    usn = serializers.CharField()
    range = serializers.CharField()
    url = serializers.CharField()
    
    def validate(self, data):
        """Just extract batch and branch info from USN"""
        usn = data['usn'].upper()
        try:
            data['batch_year'] = '20' + usn[3:5]
            data['branch_code'] = usn[5:7]
        except IndexError:
            raise serializers.ValidationError("Invalid USN structure")
        return data