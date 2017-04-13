<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
	<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'Duration'"/>
	<xsl:param name="type" select="'urn:av-openhome-org:service:Info:1'"/>

	<xsl:template match="/s:Envelope/s:Body/*[contains(local-name(), 'Response')]">
		<xsl:for-each select="*">
			<xsl:if test="local-name() = $action">
				<xsl:value-of select="."/>
			</xsl:if>
		</xsl:for-each>
	</xsl:template>
	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
