<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:e="urn:schemas-upnp-org:event-1-0">
	<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'var_list'"/>
	<xsl:param name="type" select="'Volume'"/>

	<xsl:template match="/e:propertyset/e:property">
		<xsl:choose>
			<xsl:when test="$action = 'value'">
				<xsl:for-each select="*">
					<xsl:if test="local-name() = $type">
						<xsl:value-of select="."/>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'var_list'">
				<xsl:for-each select="*">
					<xsl:value-of select="local-name()" />
					<xsl:value-of select="','" />
				</xsl:for-each>			
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
