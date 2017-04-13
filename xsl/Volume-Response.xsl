<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
	xmlns:u="urn:av-openhome-org:service:Volume:1">
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'Value'"/>
	<xsl:param name="type" select="'urn:av-openhome-org:service:Volume:1'"/>

	<xsl:template match="/s:Envelope/s:Body/*[contains(local-name(), 'Response')]">
		<xsl:choose>
			<xsl:when test="$action = 'Value'">
				<xsl:value-of select="Value"/>
			</xsl:when>
			<xsl:when test="$action = 'Uri'">
				<xsl:value-of select="Uri"/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>

