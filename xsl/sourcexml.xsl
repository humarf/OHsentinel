<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" >
	<!--:deploy:OHcli:/usr/local/share/OHcli/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>

	<xsl:template match="/SourceList">
		<xsl:for-each select="Source">
			<xsl:value-of select="count(preceding-sibling::*)" />
			<xsl:value-of select="'='" />
			<xsl:value-of select="Name" />
			<xsl:value-of select="','" />
		</xsl:for-each>
	</xsl:template>
	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
